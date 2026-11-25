# SemiAutomaticClassificationPlugin
# The Semi-Automatic Classification Plugin for QGIS allows for the supervised 
# classification of remote sensing images, providing tools for the download, 
# the preprocessing and postprocessing of images.
# begin: 2012-12-29
# Copyright (C) 2012-2026 by Luca Congedo.
# Author: Luca Congedo
# Email: ing.congedoluca@gmail.com
#
# This file is part of SemiAutomaticClassificationPlugin.
# SemiAutomaticClassificationPlugin is free software: you can redistribute it 
# and/or modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation, 
# either version 3 of the License, or (at your option) any later version.
# SemiAutomaticClassificationPlugin is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with SemiAutomaticClassificationPlugin. 
# If not, see <https://www.gnu.org/licenses/>.


import base64
import ctypes
import datetime
import json
import os
import random
import subprocess
import time
from pathlib import Path
import numpy as np

try:
    from packaging.version import parse
except Exception as error:
    str(error)

from qgis.PyQt.QtCore import Qt, QUrl, QByteArray
from qgis.PyQt.QtGui import QColor, QDesktopServices
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtWidgets import QApplication
# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsNetworkAccessManager, QgsSymbol,
    QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsPalettedRasterRenderer, QgsCoordinateReferenceSystem, QgsProject
)

try:
    from osgeo import ogr, osr
except Exception as error:
    str(error)

try:
    from scipy.spatial.distance import cdist
except Exception as error:
    str(error)

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])

""" download functions """










""" encrypt functions """


# encrypt password
def encrypt_password(password):
    e = base64.b64encode(bytes(password, 'utf-8'))
    return str(e)


# decrypt password
def decrypt_password(password):
    if password is not None:
        d = base64.b64decode(password)
        return d
    else:
        return ''


""" time functions """


# get time
def get_time():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')


# get date
def get_date():
    return datetime.datetime.now().strftime('%Y_%m_%d')


""" QGIS map and symbology functions """








# refresh vector combo
def refresh_vector_layer():
    cfg.dialog.ui.vector_name_combo.blockSignals(True)
    cfg.dialog.ui.vector_name_combo_2.blockSignals(True)
    ls = cfg.util_qgis.get_qgis_project().mapLayers().values()
    cfg.dialog.ui.shapefile_comboBox.clear()
    cfg.dialog.ui.vector_name_combo.clear()
    cfg.dialog.ui.vector_name_combo_2.clear()
    cfg.dialog.ui.reference_name_combo_3.clear()
    for layer in sorted(ls, key=lambda c: c.name()):
        if layer.type() == cfg.util_qgis.get_qgis_map_vector():
            if ((layer.wkbType() == cfg.util_qgis.get_qgis_wkb_types().Polygon)
                    or (layer.wkbType() ==
                        cfg.util_qgis.get_qgis_wkb_types().MultiPolygon)):
                cfg.dialog.shape_clip_combo(layer.name())
                cfg.dialog.vector_to_raster_combo(layer.name())
                cfg.dialog.vector_edit_raster_combo(layer.name())
                cfg.dialog.vector_zonal_raster_combo(layer.name())
    cfg.dialog.ui.vector_name_combo.blockSignals(False)
    cfg.dialog.ui.vector_name_combo_2.blockSignals(False)
    refresh_vector_fields()
    refresh_edit_raster_vector_fields()
    refresh_raster_zonal_stats_vector_fields()


# reference layer name
def refresh_vector_fields():
    reference_layer = cfg.dialog.ui.vector_name_combo.currentText()
    cfg.dialog.ui.field_comboBox.clear()
    cfg.dialog.ui.select_shapefile_label.setText('')
    cfg.dialog.ui.MC_ID_combo.clear()
    cfg.dialog.ui.MC_Info_combo.clear()
    cfg.dialog.ui.C_ID_combo.clear()
    cfg.dialog.ui.C_Info_combo.clear()
    # cfg.dialog.ui.field_comboBox_2.clear()
    layer = cfg.util_qgis.select_layer_by_name(reference_layer)
    try:
        if layer.type() == cfg.util_qgis.get_qgis_map_vector():
            f = layer.dataProvider().fields()
            for i in f:
                if str(i.typeName()).lower() != 'string':
                    cfg.dialog.reference_field_combo(str(i.name()))
    except Exception as err:
        return str(err)


# reference layer name
def refresh_edit_raster_vector_fields():
    reference_layer = cfg.dialog.ui.vector_name_combo_2.currentText()
    cfg.dialog.ui.field_comboBox_2.clear()
    layer = cfg.util_qgis.select_layer_by_name(reference_layer)
    try:
        if layer.type() == cfg.util_qgis.get_qgis_map_vector():
            f = layer.dataProvider().fields()
            for i in f:
                if str(i.typeName()).lower() != 'string':
                    cfg.dialog.reference_field_combo2(str(i.name()))
    except Exception as err:
        return str(err)


# reference layer name
def refresh_raster_zonal_stats_vector_fields():
    reference_layer = cfg.dialog.ui.reference_name_combo_3.currentText()
    cfg.dialog.ui.class_field_comboBox_4.clear()
    layer = cfg.util_qgis.select_layer_by_name(reference_layer)
    try:
        if layer.type() == cfg.util_qgis.get_qgis_map_vector():
            f = layer.dataProvider().fields()
            for i in f:
                cfg.dialog.zonal_reference_field_combo(str(i.name()))
    except Exception as err:
        return str(err)




# set classification symbology
def classification_raster_symbol(
        classification_layer, value_name_dictionary, value_color_dictionary
):
    # class list value, color, name for ramp
    # noinspection PyTypeChecker
    class_list = [QgsPalettedRasterRenderer.Class(
        0, QColor('#000000'),
        '0 - %s' % QApplication.translate('semiautomaticclassificationplugin',
                                          'Unclassified')
    )]
    for value in value_name_dictionary:
        class_list.append(
            QgsPalettedRasterRenderer.Class(
                value, QColor(value_color_dictionary[value]),
                '%s - %s' % (str(value), value_name_dictionary[value])
            )
        )
    # create the renderer
    renderer = QgsPalettedRasterRenderer(
        classification_layer.dataProvider(), 1, class_list
    )
    # apply the renderer to classLayer
    classification_layer.setRenderer(renderer)
    # refresh legend
    if hasattr(classification_layer, 'setCacheImage'):
        classification_layer.setCacheImage(None)
    classification_layer.triggerRepaint()
    cfg.util_qgis.refresh_layer_symbology(classification_layer)




""" process functions """




# check if the clicked point is inside the image
def check_point_in_image(
        point, bandset_number=None, point_crs=None,
        output_crs=None
):
    if bandset_number is None:
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get(bandset_number)
    band_count = bandset_x.get_band_count()
    if band_count == 0:
        return False
    cfg.logger.log.debug(
        'point: %s; bandset_number: %s; point_crs: %s'
        % (str(point), str(bandset_number), str(point_crs))
    )
    band_crs = str(
        cfg.bandset_catalog.get_bandset(bandset_number).bands[0].crs
    )
    band_left = cfg.bandset_catalog.get_bandset(bandset_number).bands[0].left
    band_top = cfg.bandset_catalog.get_bandset(bandset_number).bands[0].top
    band_right = cfg.bandset_catalog.get_bandset(bandset_number).bands[0].right
    band_bottom = cfg.bandset_catalog.get_bandset(bandset_number).bands[
        0].bottom
    if point_crs is None or len(point_crs) == 0:
        point_crs = cfg.util_qgis.get_qgis_crs().toWkt()
    cfg.logger.log.debug(
        'point_crs: %s; band_crs: %s' % (str(point_crs), str(band_crs))
    )
    if band_crs is not None and point_crs is not None:
        if cfg.util_gdal.compare_crs(point_crs, band_crs) is False:
            try:
                # noinspection PyTypeChecker
                point = project_qgis_point_coordinates(
                    point, point_crs, band_crs
                )
                point_crs = band_crs
                if point is False:
                    cfg.util_qgis.set_qgis_crs(band_crs)
                    cfg.logger.log.error('unable to project point')
                    return False
            # Error latitude or longitude exceeded limits
            except Exception as err:
                cfg.logger.log.error(str(err))
                return False
    if (point.x() > band_right or point.x() < band_left
            or point.y() > band_top or point.y() < band_bottom):
        cfg.logger.log.debug('point check failed')
        return False
    if output_crs is not None:
        if cfg.util_gdal.compare_crs(point_crs, output_crs) is False:
            try:
                point = project_qgis_point_coordinates(
                    point, point_crs, output_crs
                )
                if point is False:
                    cfg.logger.log.error('unable to project point')
                    return False
            # Error latitude or longitude exceeded limits
            except Exception as err:
                cfg.logger.log.error(str(err))
                return False
    cfg.logger.log.debug('point check successful')
    return point


# Project point coordinates
def project_qgis_point_coordinates(
        point, input_coordinates, output_coordinates
):
    try:
        # spatial reference
        input_sr = osr.SpatialReference()
        try:
            input_sr.ImportFromWkt(input_coordinates.toWkt())
        except Exception as err:
            input_sr.ImportFromWkt(input_coordinates)
            str(err)
        output_sr = osr.SpatialReference()
        try:
            output_sr.ImportFromWkt(output_coordinates.toWkt())
        except Exception as err:
            output_sr.ImportFromWkt(output_coordinates)
            str(err)
        # required by GDAL 3 coordinate order
        try:
            input_sr.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            output_sr.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        except Exception as err:
            str(err)
        # Coordinate Transformation
        transformation = osr.CoordinateTransformation(input_sr, output_sr)
        point_proj = ogr.Geometry(ogr.wkbPoint)
        point_proj.AddPoint(point.x(), point.y())
        point_proj.Transform(transformation)
        point_qgis = cfg.util_qgis.create_qgis_point(
            point_proj.GetX(), point_proj.GetY()
        )
        return point_qgis
    except Exception as err:
        str(err)
        return False


















""" raster color composite functions """


# set RGB color composite
def set_rgb_color_composite(composite=None, bandset_number=None):
    if ((len(cfg.rgb_combo.currentText()) > 0
         and cfg.rgb_combo.currentText() != '-') or composite is not None):
        try:
            if composite is None:
                composite = cfg.rgb_combo.currentText()
            cfg.logger.log.debug(
                'set_rgb_color_composite rgb: %s' % str(composite)
            )
            if composite is not None:
                check = create_rgb_color_composite(composite, bandset_number)
                if check:
                    if composite not in cfg.project_registry[cfg.reg_rgb_list]:
                        cfg.project_registry[cfg.reg_rgb_list].append(
                            composite
                        )
                        try:
                            rgb_list = list(
                                set(cfg.project_registry[cfg.reg_rgb_list])
                            )
                            rgb_list.remove('-')
                            rgb_list.insert(0, '-')
                        except Exception as err:
                            str(err)
                            rgb_list = list(
                                set(cfg.project_registry[cfg.reg_rgb_list])
                            )
                        cfg.project_registry[cfg.reg_rgb_list] = rgb_list
                    return True
                else:
                    return False
            else:
                return False
        except Exception as err:
            if 'string index' not in str(err):
                cfg.logger.log.error(str(err))
                cfg.mx.msg_err_4()
                return False
    else:
        return False


# remove RGB color composite
def remove_rgb_color_composite(bandset_number=None):
    if bandset_number is None:
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    virtual_raster_name = f'{cfg.virtual_bandset_name} {bandset_number}'
    cfg.util_qgis.remove_layer_by_name(virtual_raster_name)
    # the layer is named after its composition: it is removed by reference
    layer = cfg.virtual_bandset_dict.pop(bandset_number, None)
    if layer is not None:
        try:
            project = cfg.util_qgis.get_qgis_project()
            if project.mapLayer(layer.id()) is not None:
                project.removeMapLayer(layer.id())
        except RuntimeError:
            pass


# create RGB color composite
def create_rgb_color_composite(color_composite, bandset_number=None):
    if bandset_number is None:
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    cfg.logger.log.debug(f'create_rgb_color_composite bandset: '
                         f'{bandset_number}')
    virtual_raster_name = f'{cfg.virtual_bandset_name} {bandset_number}'
    if bandset_number in cfg.virtual_bandset_dict:
        # the layer is named after its composition: it is found by reference
        layer = cfg.virtual_bandset_dict[bandset_number]
        try:
            if cfg.util_qgis.get_qgis_project().mapLayer(
                    layer.id()) is None:
                layer = None
        except RuntimeError:
            layer = None
    else:
        bandset_x = cfg.bandset_catalog.get(bandset_number)
        if bandset_x is None:
            layer = None
        else:
            band_count = bandset_x.get_band_count()
            if band_count == 0:
                cfg.logger.log.debug('empty bandset')
                return False
            # create temporary virtual raster
            virtual_raster_path = cfg.bandset_catalog.create_virtual_raster(
                bandset_number=bandset_number
            )
            cfg.util_qgis.remove_layer_by_name(virtual_raster_name)
            layer = cfg.iface.addRasterLayer(
                virtual_raster_path, virtual_raster_name
            )
    # get band numbers
    composite = str(color_composite).split(',')
    if len(composite) == 1:
        composite = str(color_composite).split('-')
    if len(composite) == 1:
        composite = str(color_composite).split(';')
    if len(composite) == 1:
        composite = str(color_composite)
    if layer is None:
        if bandset_number in cfg.virtual_bandset_dict:
            del cfg.virtual_bandset_dict[bandset_number]
        cfg.logger.log.error('create_rgb_color_composite')
        return False
    elif len(composite) < 3:
        cfg.logger.log.error('create_rgb_color_composite')
        return False
    else:
        cfg.virtual_bandset_dict[bandset_number] = layer
        bandset_x = cfg.bandset_catalog.get_bandset_by_number(bandset_number)
        count = bandset_x.get_band_count()
        try:
            if int(composite[0]) > count:
                composite[0] = count
            if int(composite[1]) > count:
                composite[1] = count
            if int(composite[2]) > count:
                composite[2] = count
        except Exception as err:
            cfg.logger.log.error(str(err))
            return False
        cfg.logger.log.error(
            'create_rgb_color_composite: %s-%s-%s'
            % (str(composite[0]), str(composite[1]), str(composite[2]))
        )
        QApplication.instance().processEvents()
        cfg.util_qgis.set_raster_color_composite(
            layer, int(composite[0]), int(composite[1]), int(composite[2])
        )
        # the layer takes the name of the composition
        if cfg.composition_layer_name:
            layer.setName(cfg.composition_layer_name)
        return True


""" general functions """


# read variables from project instance
def read_project_variables():
    for r in cfg.project_registry:
        try:
            cfg.project_registry[r] = cfg.util_qgis.read_project_variable(
                r, cfg.project_registry[r]
            )
        except Exception as err:
            cfg.logger.log.debug('error: %s' % str(err))
    cfg.logger.log.debug('project_registry: %s' % str(cfg.project_registry))
    # set RGB list
    cfg.util_qt.set_combobox_items(
        cfg.rgb_combo, cfg.project_registry[cfg.reg_rgb_list]
    )
    cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_ID_spin.setValue(
        int(cfg.project_registry[cfg.reg_roi_macroclass_id])
    )
    cfg.project_registry[cfg.reg_roi_macroclass_name] = (
        cfg.project_registry)[cfg.reg_roi_class_name]
    # ROI macroclass info field
    cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_line.setText(
        cfg.project_registry[cfg.reg_roi_macroclass_name]
    )
    # restore active bandset number
    active_bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    # bandset restore
    for bandset_number in range(
            1, cfg.project_registry[cfg.reg_bandset_count] + 1
    ):
        cfg.logger.log.debug('bandset restore: %s' % str(bandset_number))
        bandset_key = '%s%s' % (cfg.reg_bandset, bandset_number)
        # import xml
        xml_file = cfg.rs.configurations.temp.temporary_file_path(
            name_suffix='.xml'
        )
        xml = cfg.util_qgis.read_project_variable(bandset_key, '')
        with open(xml_file, 'w') as output_file:
            output_file.write(xml)
        # add empty bandset
        cfg.bst.add_band_set_tab(position=bandset_number)
        try:
            cfg.bandset_catalog.import_bandset_from_xml(
                bandset_number=bandset_number, xml_path=xml_file
            )
        except Exception as err:
            str(err)
        cfg.bst.band_set_to_table(bandset_number)
    active_bandset_number = 1
    cfg.project_registry[cfg.reg_active_bandset_number] = 1
    cfg.logger.log.debug('bandset restore simplified')
    # add empty bandset
    cfg.bst.add_band_set_tab_simplified()
    cfg.bst.band_set_to_table_simplified()
    cfg.dialog.ui.bandset_number_spinBox.setValue(active_bandset_number)
    # training path restore
    if len(cfg.project_registry[cfg.reg_training_input_path]) > 0:
        cfg.scp_dock.open_signature_catalog_file(
            cfg.project_registry[cfg.reg_training_input_path],
            cfg.project_registry[cfg.reg_training_bandset_number]
        )
    # download table restore
    cfg.download_products.open_download_table()


# find available RAM
# noinspection SpellCheckingInspection
def find_available_ram():
    try:
        if cfg.system_platform.startswith('win'):
            class GlobalMemoryStatus(ctypes.Structure):
                _fields_ = [
                    ('length', ctypes.c_ulong), ('memoryLoad', ctypes.c_ulong),
                    ('totalRam', ctypes.c_ulong),
                    ('availPhys', ctypes.c_ulonglong),
                    ('totalPageFile', ctypes.c_ulonglong),
                    ('availPageFile', ctypes.c_ulonglong),
                    ('totalVirt', ctypes.c_ulonglong),
                    ('availVirt', ctypes.c_ulonglong),
                    ('availExVirt', ctypes.c_ulonglong)
                ]

            memory_status = GlobalMemoryStatus()
            # noinspection PyUnresolvedReferences
            ctypes.windll.kernel32.GlobalMemoryStatus(
                ctypes.byref(memory_status)
            )
            ram_value = memory_status.totalRam
            cfg.qgis_registry[cfg.reg_ram_value] = int(
                (ram_value / 1048576) / 2
            )
        elif cfg.system_platform.startswith('darwin'):
            cfg.qgis_registry[cfg.reg_ram_value] = 2048
        else:
            with open('/proc/meminfo') as info:
                for line in info:
                    if line.startswith('MemTotal'):
                        ram_value = line.split()[1]
                        break
            cfg.qgis_registry[cfg.reg_ram_value] = int(
                (int(ram_value) / 1000) / 2
            )
        cfg.dialog.ui.RAM_spinBox.setValue(
            cfg.qgis_registry[cfg.reg_ram_value]
        )
    except Exception as err:
        str(err)


# find available processors
def find_available_processors():
    try:
        threads = os.cpu_count()
        cfg.dialog.ui.CPU_spinBox.setValue(int((threads + 1) / 2))
    except Exception as err:
        str(err)
        cfg.dialog.ui.CPU_spinBox.setValue(2)




# get random integer
def random_integer(minimum, maximum):
    return random.randint(minimum, maximum)


# get random color
def random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return '#%02x%02x%02x' % (r, g, b)


# remove file
def remove_file(file_path):
    if file_path is not None:
        os.remove(file_path)


# check if file exists
def check_file(file_path):
    if file_path is None:
        return False
    else:
        return os.path.isfile(file_path)


# get parent directory name
def directory_name(file_path):
    if file_path is not None:
        return os.path.dirname(file_path)
    return None


# get base name
def base_name(file_path):
    if file_path is not None:
        return os.path.basename(file_path)
    return None


# relative path
def absolute_to_relative(path, root=None):
    p = Path(path)
    try:
        relative = p.relative_to(root)
    except Exception as err:
        str(err)
        relative = p
    return relative.as_posix()


# absolute path
def relative_to_absolute_path(path, root=None):
    if root is None:
        absolute = path
    else:
        absolute = '/'.join([root, path]).replace('\\', '/').replace(
            '//', '/'
        ).replace('/\\', '/').replace('//', '/')
    return absolute


# Try to get GDAL for macOS
def get_gdal_path_for_mac():
    if cfg.system_platform.startswith('darwin'):
        gdal_line = cfg.qgis_registry[cfg.reg_gdal_path]
        if len(gdal_line) > 0:
            cfg.qgis_registry[cfg.reg_gdal_path] = gdal_line.rstrip('/') + '/'
            if not check_file(
                    cfg.qgis_registry[cfg.reg_gdal_path] + 'gdal_translate'
            ):
                cfg.qgis_registry[cfg.reg_gdal_path] = ''
        else:
            v = cfg.util_gdal.get_gdal_version()
            cfg.qgis_registry[cfg.reg_gdal_path] = (
                    '/Library/Frameworks/GDAL.framework/Versions/'
                    '%s.%s/Programs/' % (v[0], v[1])
            )
            if not check_file(
                    cfg.qgis_registry[cfg.reg_gdal_path] + 'gdal_translate'
            ):
                cfg.qgis_registry[cfg.reg_gdal_path] = ''
