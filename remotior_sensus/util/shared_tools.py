# Remotior Sensus , software to process remote sensing and GIS data.
# Copyright (C) 2022-2026 Luca Congedo.
# Author: Luca Congedo
# Email: ing.congedoluca@gmail.com
#
# This file is part of Remotior Sensus.
# Remotior Sensus is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
# Remotior Sensus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Remotior Sensus. If not, see <https://www.gnu.org/licenses/>.

"""
Shared tools
"""

import re
import inspect
from os import path
from random import randint
from typing import Union, Optional
from itertools import chain
import numpy as np

try:
    from scipy.ndimage import label
except Exception as error:
    str(error)

from remotior_sensus.core import configurations as cfg
from remotior_sensus.core.bandset_catalog import BandSet, BandSetCatalog
from remotior_sensus.util import files_directories, raster_vector
from remotior_sensus.core.processor_functions import region_growing


# check input path converting to the same crs if necessary
def prepare_input_list(
        band_list, reference_raster_crs=None,
        n_processes: int = None, src_nodata=None, dst_nodata=None,
        raster_bands=None
):
    log = cfg.logger.log
    log.debug('start')
    log.debug('band_list: %s' % str(band_list))
    information_list = []
    nodata_list = []
    if band_list is None or len(band_list) == 0:
        log.error('empty list')
        return {
            'input_list': [], 'information_list': [], 'nodata_list': [],
            'name_list': [], 'warped': None, 'same_geotransformation': None,
            'box_coordinates_list': None
        }
    try:
        if reference_raster_crs is None:
            reference_raster_crs = raster_vector.get_crs(band_list[0])
        # get crs from file
        elif files_directories.is_file(reference_raster_crs):
            reference_raster_crs = raster_vector.get_crs(reference_raster_crs)
    except Exception as err:
        log.error(str(err))
        log.error(
            'unable to get raster: %s' % band_list[0]
        )
        return {
            'input_list': [], 'information_list': [], 'nodata_list': [],
            'name_list': [], 'warped': None, 'same_geotransformation': None,
            'box_coordinates_list': None
        }
    input_list = []
    name_list = []
    gt_list = []
    xy_count_list = []
    box_coordinates_list = []
    warped = False
    first_gt = first_xy_count = check_gt = check_xy_count = None
    for i, band_i in enumerate(band_list):
        info = raster_vector.raster_info(band_i)
        if info is not False:
            (gt, crs, un, xy_count, nd, number_of_bands, block_size,
             scale_offset, data_type) = info
        else:
            log.error(
                'unable to get raster info: %s' % band_i
            )
            return {
                'input_list': [], 'information_list': [], 'nodata_list': [],
                'name_list': [], 'warped': None,
                'same_geotransformation': None, 'box_coordinates_list': None
            }
        crs = raster_vector.get_crs(band_i)
        # check crs
        same_crs = raster_vector.compare_crs(crs, reference_raster_crs)
        if not same_crs:
            t_pmd = cfg.temp.temporary_raster_path(
                name=files_directories.file_name(band_i),
                extension=cfg.vrt_suffix
            )
            reference_raster = cfg.multiprocess.create_warped_vrt(
                raster_path=band_i, output_path=t_pmd,
                output_wkt=str(reference_raster_crs), n_processes=n_processes,
                src_nodata=src_nodata, dst_nodata=dst_nodata
            )
            warped = True
        else:
            reference_raster = band_i
        if raster_bands is None:
            name_list.append(files_directories.file_name(band_i))
        else:
            raster_band = raster_bands[i]
            if number_of_bands > 1:
                reference_raster = (
                    raster_vector.create_temporary_virtual_raster(
                        input_raster_list=[band_i],
                        band_number_list=[[raster_band]]
                    )
                )
                name_list.append(
                    '%s_%s' % (files_directories.file_name(band_i),
                               raster_band)
                )
            else:
                name_list.append(files_directories.file_name(band_i))
        input_list.append(reference_raster)
        information_list.append(
            [gt, crs, un, xy_count, nd, number_of_bands, block_size,
             scale_offset, data_type]
        )
        gt_list.append(gt)
        xy_count_list.append(xy_count)
        nodata_list.append(nd)
        top = gt[3]
        left = gt[0]
        bottom = gt[3] + gt[5] * xy_count[1] + gt[4] * xy_count[0]
        right = gt[0] + gt[1] * xy_count[0] + gt[2] * xy_count[1]
        box_coordinates_list.append([left, top, right, bottom])
        if first_gt is None:
            first_gt = gt
            first_xy_count = xy_count
        else:
            if gt != first_gt:
                check_gt = False
            if xy_count != first_xy_count:
                check_xy_count = False
    # check if same geotransformation, x and y pixel count
    if check_gt is True and check_xy_count is True and warped is False:
        same_geotransformation = True
    else:
        same_geotransformation = False
    log.debug('end; input_list: %s' % str(input_list))
    prepared = {
        'input_list': input_list, 'information_list': information_list,
        'nodata_list': nodata_list, 'name_list': name_list,
        'warped': warped, 'same_geotransformation': same_geotransformation,
        'box_coordinates_list': box_coordinates_list
    }
    return prepared


# prepare process files
def prepare_process_files(
        input_bands: Union[list, int, BandSet],
        output_path: Optional[str] = None,
        n_processes: Optional[int] = None, overwrite=False,
        bandset_catalog: Optional[BandSetCatalog] = None,
        temporary_virtual_raster=True, prefix=None, multiple_output=False,
        multiple_input=False, multiple_resolution=False,
        virtual_output=None, box_coordinate_list: Optional[list] = None
):
    log = cfg.logger.log
    log.debug('input_bands: %s' % str(input_bands))
    if n_processes is None:
        n_processes = cfg.n_processes
    # get input list
    band_list = BandSetCatalog.get_band_list(input_bands, bandset_catalog)
    raster_bands = None
    if type(input_bands) is BandSet:
        coord_list = input_bands.box_coordinate_list
        if coord_list is not None:
            box_coordinate_list = coord_list
        raster_bands = input_bands.bands['raster_band'].tolist()
    elif type(input_bands) is int:
        coord_list = bandset_catalog.get_bandset(
            bandset_number=input_bands
        ).box_coordinate_list
        if coord_list is not None:
            box_coordinate_list = coord_list
    # list of inputs
    prepared_input = prepare_input_list(
        band_list, n_processes=n_processes, raster_bands=raster_bands
    )
    input_raster_list = prepared_input['input_list']
    if len(input_raster_list) == 0:
        return {
            'input_raster_list': [], 'output_path': None,
            'virtual_output': None,
            'n_processes': None, 'same_geotransformation': None
        }
    raster_info = prepared_input['information_list']
    nodata_list = prepared_input['nodata_list']
    name_list = prepared_input['name_list']
    warped = prepared_input['warped']
    same_geotransformation = prepared_input['same_geotransformation']
    box_coordinates_list = prepared_input['box_coordinates_list']
    # single output path
    out_path = None
    # multiple output path list
    output_list = []
    # multiple output virtual raster check list
    vrt_list = []
    if multiple_output:
        if output_path is None:
            output_path = [
                cfg.temp.temporary_raster_path(name=_r,
                                               extension=cfg.vrt_suffix)
                for _r in name_list
            ]
        if type(output_path) is not list and type(output_path) is not tuple:
            if not files_directories.is_directory(output_path):
                files_directories.create_directory(output_path)
            for _r in name_list:
                p = path.join(
                    output_path, '{}{}'.format(prefix, _r)
                ).replace('\\', '/')
                # check output path
                out_path, vrt_r = files_directories.raster_output_path(
                    p, virtual_output
                )
                output_list.append(out_path)
                vrt_list.append(vrt_r)
        else:
            for r in output_path:
                # check output path
                out_path, vrt_r = files_directories.raster_output_path(
                    r, virtual_output
                )
                output_list.append(out_path)
                vrt_list.append(vrt_r)
    else:
        if output_path is None:
            output_path = cfg.temp.temporary_raster_path(
                extension=cfg.vrt_suffix
            )
        # check output path
        try:
            out_path, virtual_output = files_directories.raster_output_path(
                output_path, virtual_output, overwrite=overwrite
            )
        except Exception as err:
            log.error(str(err))
            if not overwrite and 'existing path' in str(err):
                raise Exception(str(err))
    # create virtual raster of input
    if temporary_virtual_raster or box_coordinate_list is not None:
        # if rasters with same dimension don't create virtual raster but list
        if same_geotransformation is True and box_coordinate_list is None:
            temporary_virtual_raster = input_raster_list
        else:
            if multiple_input:
                temp_list = []
                if box_coordinate_list is None:
                    box_coordinate_list = box_coordinates_list[0]
                for r in input_raster_list:
                    if multiple_resolution:
                        temporary_virtual_raster = (
                            raster_vector.create_temporary_virtual_raster(
                                input_raster_list=[r],
                                box_coordinate_list=box_coordinate_list
                            )
                        )
                    # use first raster resolution
                    else:
                        temporary_virtual_raster = (
                            raster_vector.create_temporary_virtual_raster(
                                input_raster_list=[r],
                                box_coordinate_list=box_coordinate_list,
                                grid_reference=input_raster_list[0]
                            )
                        )
                    temp_list.append(temporary_virtual_raster)
                input_raster_list = temp_list
                temporary_virtual_raster = True
            else:
                temporary_virtual_raster = (
                    raster_vector.create_temporary_virtual_raster(
                        input_raster_list=input_raster_list,
                        box_coordinate_list=box_coordinate_list
                    )
                )
    prepared = {
        'input_raster_list': input_raster_list, 'raster_info': raster_info,
        'nodata_list': nodata_list, 'name_list': name_list, 'warped': warped,
        'output_path': out_path, 'virtual_output': virtual_output,
        'temporary_virtual_raster': temporary_virtual_raster,
        'n_processes': n_processes, 'output_list': output_list,
        'vrt_list': vrt_list, 'same_geotransformation': same_geotransformation
    }
    prepared = mpi_bcast(prepared)
    return prepared








# convert data type from string to numpy
def data_type_conversion(data_type):
    data_types = {
        cfg.float64_dt: np.float64, cfg.float32_dt: np.float32,
        cfg.int32_dt: np.int32, cfg.uint32_dt: np.uint32,
        cfg.int16_dt: np.int16, cfg.uint16_dt: np.uint16,
        cfg.byte_dt: np.uint8,
    }
    if data_type in data_types:
        return data_types[data_type]
    else:
        return None


# expand list of lists
def expand_list(input_list):
    expanded_list = list(chain.from_iterable(input_list))
    return expanded_list


# join path
def join_path(*argv):
    # noinspection PyArgumentList
    joined_path = path.join(*argv)
    return joined_path


# replace ignoring case
def replace(input_string: str, old_value: str, new_value: str):
    old_value = old_value.replace('*', '\\*').replace(
        '(', '\\('
    ).replace(')', '\\)')
    output = re.sub(old_value, new_value, input_string, flags=re.IGNORECASE)
    return output








# get random color
def random_color():
    red = randint(0, 255)
    green = randint(0, 255)
    blue = randint(0, 255)
    return "#%02x%02x%02x" % (red, green, blue)


# calculate Bray-Curtis similarity
# (100 - 100 * sum(abs(x[ki]-x[kj]) / (sum(x[ki] + x[kj])))
def calculate_bray_curtis_similarity(values_x, values_y):
    try:
        array_i = np.array(values_x)
        array_j = np.array(values_y)
        sum_i_j = array_i.sum() + array_j.sum()
        absolute = np.sqrt((array_i - array_j) ** 2)
        value = 100 - absolute.sum() / sum_i_j * 100
    except Exception as err:
        str(err)
        value = cfg.not_available
    return value


# calculate Euclidean distance sqrt(sum((x[ki] - x[kj])^2))
def calculate_euclidean_distance(values_x, values_y):
    try:
        difference = (values_x - values_y) ** 2
        value = np.sqrt(difference.sum())
    except Exception as err:
        str(err)
        value = cfg.not_available
    return value


# calculate Spectral angle
# [ arccos( sum(r_i * s_i) / sqrt( sum(r_i**2) * sum(s_i**2) ) ) ]
def calculate_spectral_angle(values_x, values_y):
    try:
        value = np.arccos(
            (values_x * values_y).sum() / np.sqrt(
                (values_x ** 2).sum() * (values_y ** 2).sum()
            )
        ) * 180 / np.pi
    except Exception as err:
        str(err)
        value = cfg.not_available
    return value


# project point coordinates from wkt or EPSG
def project_point_coordinates(
        point_x, point_y, input_coordinates, output_coordinates
) -> Union[None, list]:
    input_coord = raster_vector.get_projection_from_epsg_wkt(input_coordinates)
    output_coord = raster_vector.get_projection_from_epsg_wkt(
        output_coordinates
    )
    if input_coord is not None and output_coord is not None:
        coordinates = raster_vector.project_point_coordinates(
            point_x, point_y, input_coord, output_coord
        )
    else:
        coordinates = False
        log = cfg.logger.log
        log.error('no coordinates')
    return coordinates








# get vector fields
def get_vector_fields(input_layer):
    fields = raster_vector.get_vector_fields(input_layer)
    return fields






# get raster data
def get_colored_raster(input_raster, value_color_dictionary):
    data = raster_vector.get_colored_raster(
        path=input_raster, value_color_dictionary=value_color_dictionary
    )
    return data






def mpi_bcast(value):
    if cfg.mpi_comm:
        cfg.mpi_bcast_id += 1
        frame = inspect.stack()[1]
        func_name = frame.function
        line = frame.lineno
        log = cfg.logger.log
        log.debug(f'bcast {cfg.mpi_bcast_id} {func_name}[{line}]: '
                  f'rank {cfg.mpi_rank}, {value}')
        value = cfg.mpi_comm.bcast(value, root=0)
    return value
