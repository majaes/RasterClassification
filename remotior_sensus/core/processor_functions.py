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

import os
from contextlib import redirect_stdout

import numpy as np
from numpy.lib import stride_tricks

from remotior_sensus.core import configurations as cfg
from remotior_sensus.util import raster_vector

try:
    # noinspection PyPackageRequirements
    from sklearn.model_selection import cross_val_score, StratifiedKFold
except Exception as error:
    str(error)
try:
    # noinspection PyPackageRequirements
    import scipy.stats.distributions as statdistr
except Exception as error:
    str(error)
try:
    # noinspection PyPackageRequirements
    from scipy import signal
    # noinspection PyPackageRequirements
    from scipy.stats import mode as scipy_mode
    # noinspection PyPackageRequirements
    from scipy.ndimage import label
except Exception as error:
    str(error)

try:
    # noinspection PyPackageRequirements
    from scipy.ndimage import maximum_filter
    # noinspection PyPackageRequirements
    from scipy.ndimage import minimum_filter
    # noinspection PyPackageRequirements
    from scipy.ndimage import percentile_filter
    # noinspection PyPackageRequirements
    from scipy.ndimage import generic_filter
    # noinspection PyPackageRequirements
    from scipy.ndimage import median_filter
except Exception as error:
    str(error)
    # for backward compatibility
    try:
        # noinspection PyPackageRequirements
        from scipy.ndimage.filters import maximum_filter
        # noinspection PyPackageRequirements
        from scipy.ndimage.filters import minimum_filter
        # noinspection PyPackageRequirements
        from scipy.ndimage.filters import percentile_filter
        # noinspection PyPackageRequirements
        from scipy.ndimage.filters import generic_filter
        # noinspection PyPackageRequirements
        from scipy.ndimage.filters import median_filter
    except Exception as error:
        str(error)

try:
    import torch
    from remotior_sensus.util.pytorch_tools import (
        train_pytorch_model, pretrained_pytorch_model_swin2,
        segmentation_pytorch_model_swin2, superresolution_pytorch_model_s2
    )
except Exception as error:
    str(error)


# function to calculate percentile with the closest observation for band_calc
def percentile_calc(array, percentile=90, axis=0):
    if type(array) is list:
        array = np.stack(array)
    # count values that are not nan
    value_count = np.sum(~np.isnan(array), axis=axis)
    # sort array
    sorted_array = np.sort(array, axis=axis)
    # calculate percentile index
    perc_index = np.round(
        (value_count - 1) * float(percentile) / 100
    ).astype(int)
    # get percentile values
    result = np.take_along_axis(
        sorted_array, np.expand_dims(perc_index, axis=axis), axis=axis
    ).squeeze(axis)
    return result




# band calculation
# noinspection PyShadowingBuiltins,PyUnusedLocal
def band_calculation(*argv):
    # array variable name as defined in cfg.array_function_placeholder
    output_no_data = argv[0][2]
    _array = argv[1][0]
    _array_mask = argv[1][1]
    _array_function_placeholder = np.ma.array(_array, mask=_array_mask)
    nodata_mask = argv[2]
    function_argument = argv[7]
    # expose numpy functions
    namespace = {
        '_array_function_placeholder': _array_function_placeholder,
        'np': np, 'ma': np.ma, 'log': np.ma.log, 'log10': np.ma.log10,
        'sqrt': np.ma.sqrt, 'cos': np.ma.cos, 'arccos': np.ma.arccos,
        'sin': np.ma.sin, 'arcsin': np.ma.arcsin, 'tan': np.ma.tan,
        'arctan': np.ma.arctan, 'exp': np.ma.exp, 'min': np.ma.min,
        'max': np.ma.max, 'sum': np.ma.sum, 'percentile': percentile_calc,
        'median': np.ma.median, 'mean': np.ma.mean, 'std': np.ma.std,
        'where': np.ma.where, 'nan': np.nan,
    }
    log = cfg.logger.log
    log.debug('function_argument: %s' % str(function_argument))
    log.debug(
        '_array_function_placeholder.shape: %s; type: %s'
        % (str(_array_function_placeholder.shape),
           type(_array_function_placeholder))
    )
    # perform operation
    try:
        _o: np.ma.core.MaskedArray = eval(function_argument,
                                          {'__builtins__': None}, namespace)
    except Exception as err:
        log.error(str(err))
        return False
    # if not array
    # noinspection PyUnreachableCode
    if (not isinstance(_o, np.ma.core.MaskedArray)
            and not isinstance(_o, np.ndarray)):
        log.error('not array ' + str(type(_o)))
        return False
    # check nodata
    log.debug(
        '_o.shape: %s; _o.n_bytes: %s; _o.dtype: %s'
        % (str(_o.shape), str(_o.nbytes), str(_o.dtype))
    )
    if _o.dtype == bool:
        _o = _o.astype(int)
    # replace nodata
    _o[nodata_mask == 1] = output_no_data
    return [[_o.data, _o.mask], None]




# classification maximum likelihood
def classification_maximum_likelihood(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    # function argument
    signatures = argv[7][cfg.spectral_signatures_framework]
    # get selected signatures
    signatures_table = signatures.table[signatures.table.selected == 1]
    covariance_matrices = argv[7][cfg.covariance_matrices_framework]
    normalization = argv[7][cfg.normalization_values_framework]
    function_variable_list = argv[8]
    macroclass = function_variable_list[0]
    threshold = function_variable_list[1]
    ro_x, ro_y = argv[10]
    output_signature_raster = argv[11]
    out_class = argv[12]
    out_alg = argv[13]
    previous_array = None
    classification_array = None
    log = cfg.logger.log
    if normalization[0] is not None:
        for n in range(0, _array_function_placeholder.shape[2]):
            _array_function_placeholder[::, ::, n] = eval(normalization[0][n])
    for s in signatures_table.signature_id.tolist():
        if macroclass:
            class_id = signatures_table[
                signatures_table.signature_id == s].macroclass_id
        else:
            class_id = signatures_table[
                signatures_table.signature_id == s].class_id
        values = signatures.signatures[s].value
        if _array_function_placeholder.shape[2] < values.shape[0]:
            values = values[0:_array_function_placeholder.shape[2]]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        elif _array_function_placeholder.shape[2] > values.shape[0]:
            _array_function_placeholder = _array_function_placeholder[
                                          :, :, 0:values.shape[0]
                                          ]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        log.debug('signature: %s; values: %s' % (s, str(values)))
        try:
            cov_matrix = covariance_matrices[s]
            # natural logarithm of the determinant of covariance matrix
            (sign, log_det) = np.linalg.slogdet(cov_matrix)
            inverse_cov_matrix = np.linalg.inv(cov_matrix)
            d = _array_function_placeholder - values
            distance_array = - log_det - (
                    np.dot(d, inverse_cov_matrix) * d).sum(axis=2)
            if threshold is True:
                class_threshold = signatures_table[
                    signatures_table.signature_id == s].min_dist_thr
                p = class_threshold / 100
                chi = statdistr.chi2.isf(p, cov_matrix.shape[0])
                chi_threshold = -2 * chi - log_det
                distance_array[distance_array < chi_threshold] = cfg.nodata_val
            elif threshold is not False and threshold is not None:
                p = threshold / 100
                chi = statdistr.chi2.isf(p, cov_matrix.shape[0])
                chi_threshold = -2 * chi - log_det
                distance_array[distance_array < chi_threshold] = cfg.nodata_val
            if previous_array is None:
                previous_array = distance_array
                classification_array = np.ones(
                    (_array_function_placeholder.shape[0],
                     _array_function_placeholder.shape[1])
                ) * class_id
                classification_array[
                    distance_array == cfg.nodata_val] = output_no_data
            else:
                maximum_array = np.maximum(distance_array, previous_array)
                maximum_array[
                    maximum_array == cfg.nodata_val] = previous_array[
                    maximum_array == cfg.nodata_val]
                classification_array[
                    maximum_array != previous_array] = class_id
                classification_array[
                    maximum_array == cfg.nodata_val] = output_no_data
                previous_array = maximum_array
            if len(output_signature_raster) > 0:
                distance_array[
                    (distance_array == cfg.nodata_val) | (nodata_mask == 1)
                ] = output_no_data
                write_sig = raster_vector.write_raster(
                    output_signature_raster[s], x - ro_x, y - ro_y,
                    distance_array, output_no_data, scale, offset
                )
                log.debug('write_sig: %s' % str(write_sig))
        except Exception as err:
            log.error(str(err))
    if classification_array is not None:
        # write classification
        classification_array[
            (classification_array == cfg.nodata_val) | (nodata_mask == 1)
        ] = output_no_data
        write_class = raster_vector.write_raster(
            out_class, x - ro_x, y - ro_y, classification_array,
            output_no_data, scale, offset
        )
        log.debug('write_class: %s' % str(write_class))
        # write the algorithm raster
        if out_alg is not None:
            previous_array[
                (classification_array == cfg.nodata_val) | (nodata_mask == 1)
            ] = output_no_data
            write_alg = raster_vector.write_raster(
                out_alg, x - ro_x, y - ro_y, previous_array, output_no_data,
                scale, offset
            )
            log.debug('write_alg: %s' % str(write_alg))
        log.debug(
            'classification_array.shape: %s' % str(classification_array.shape)
        )
        return [True, out_class]
    else:
        return [False, out_class]


# classification minimum distance
def classification_minimum_distance(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    signatures = argv[7][cfg.spectral_signatures_framework]
    # get selected signatures
    signatures_table = signatures.table[signatures.table.selected == 1]
    normalization = argv[7][cfg.normalization_values_framework]
    function_variable_list = argv[8]
    macroclass = function_variable_list[0]
    threshold = function_variable_list[1]
    ro_x, ro_y = argv[10]
    output_signature_raster = argv[11]
    out_class = argv[12]
    out_alg = argv[13]
    previous_array = None
    classification_array = None
    log = cfg.logger.log
    if normalization[0] is not None:
        for n in range(0, _array_function_placeholder.shape[2]):
            _array_function_placeholder[::, ::, n] = eval(normalization[0][n])
    for s in signatures_table.signature_id.tolist():
        if macroclass:
            class_id = signatures_table[
                signatures_table.signature_id == s].macroclass_id
        else:
            class_id = signatures_table[
                signatures_table.signature_id == s].class_id
        values = signatures.signatures[s].value
        if _array_function_placeholder.shape[2] < values.shape[0]:
            values = values[0:_array_function_placeholder.shape[2]]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        elif _array_function_placeholder.shape[2] > values.shape[0]:
            _array_function_placeholder = _array_function_placeholder[
                                          :, :, 0:values.shape[0]
                                          ]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        # Euclidean distance
        distance_array = np.sqrt(
            ((_array_function_placeholder - values) ** 2).sum(axis=2)
        )
        if threshold is True:
            class_threshold = signatures_table[
                signatures_table.signature_id == s].min_dist_thr
            distance_array[
                distance_array < class_threshold] = cfg.nodata_val_Int32
        elif threshold is not False and threshold is not None:
            distance_array[
                distance_array < threshold] = cfg.nodata_val_Int32
        if previous_array is None:
            previous_array = distance_array
            classification_array = np.ones(
                (_array_function_placeholder.shape[0],
                 _array_function_placeholder.shape[1])
            ) * class_id
        else:
            minimum_array = np.minimum(distance_array, previous_array)
            classification_array[minimum_array != previous_array] = class_id
            previous_array = minimum_array
        classification_array[
            distance_array == cfg.nodata_val_Int32] = output_no_data
        if len(output_signature_raster) > 0:
            distance_array[
                (distance_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
            ] = output_no_data
            write_sig = raster_vector.write_raster(
                output_signature_raster[s], x - ro_x, y - ro_y, distance_array,
                output_no_data, scale, offset
            )
            log.debug('write_sig: %s' % str(write_sig))
    # write classification
    classification_array[
        (classification_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
    ] = output_no_data
    write_class = raster_vector.write_raster(
        out_class, x - ro_x, y - ro_y, classification_array, output_no_data,
        scale, offset
    )
    log.debug('write_class: %s' % str(write_class))
    # write the algorithm raster
    if out_alg is not None:
        previous_array[
            (classification_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
        ] = output_no_data
        write_alg = raster_vector.write_raster(
            out_alg, x - ro_x, y - ro_y, previous_array, output_no_data, scale,
            offset
        )
        log.debug('write_alg: %s' % str(write_alg))
    log.debug(
        'classification_array.shape: %s' % str(classification_array.shape)
    )
    return [True, out_class]


# classification spectral angle mapping
def classification_spectral_angle_mapping(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    signatures = argv[7][cfg.spectral_signatures_framework]
    # get selected signatures
    signatures_table = signatures.table[signatures.table.selected == 1]
    normalization = argv[7][cfg.normalization_values_framework]
    function_variable_list = argv[8]
    macroclass = function_variable_list[0]
    threshold = function_variable_list[1]
    ro_x, ro_y = argv[10]
    output_signature_raster = argv[11]
    out_class = argv[12]
    out_alg = argv[13]
    previous_array = None
    classification_array = None
    log = cfg.logger.log
    if normalization[0] is not None:
        for n in range(0, _array_function_placeholder.shape[2]):
            _array_function_placeholder[::, ::, n] = eval(normalization[0][n])
    for s in signatures_table.signature_id.tolist():
        if macroclass:
            class_id = signatures_table[
                signatures_table.signature_id == s].macroclass_id
        else:
            class_id = signatures_table[
                signatures_table.signature_id == s].class_id
        values = signatures.signatures[s].value
        if _array_function_placeholder.shape[2] < values.shape[0]:
            values = values[0:_array_function_placeholder.shape[2]]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        elif _array_function_placeholder.shape[2] > values.shape[0]:
            _array_function_placeholder = _array_function_placeholder[
                                          :, :, 0:values.shape[0]
                                          ]
            log.error(
                'signature values shape; trying to continue anyway'
            )
        # spectral angle
        distance_array = np.arccos(
            (_array_function_placeholder * values).sum(axis=2) / np.sqrt(
                (_array_function_placeholder ** 2).sum(axis=2) * (
                        values ** 2).sum()
            )
        ) * 180 / np.pi
        if threshold is True:
            class_threshold = signatures_table[
                signatures_table.signature_id == s].min_dist_thr
            distance_array[
                distance_array < class_threshold] = cfg.nodata_val_Int32
        elif threshold is not False and threshold is not None:
            distance_array[
                distance_array < threshold] = cfg.nodata_val_Int32
        if previous_array is None:
            previous_array = distance_array
            classification_array = np.ones(
                (_array_function_placeholder.shape[0],
                 _array_function_placeholder.shape[1])
            ) * class_id
        else:
            minimum_array = np.minimum(distance_array, previous_array)
            classification_array[minimum_array != previous_array] = class_id
            previous_array = minimum_array
        classification_array[
            distance_array == cfg.nodata_val_Int32] = output_no_data
        if len(output_signature_raster) > 0:
            distance_array[
                (distance_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
            ] = output_no_data
            write_sig = raster_vector.write_raster(
                output_signature_raster[s], x - ro_x, y - ro_y, distance_array,
                output_no_data, scale, offset
            )
            log.debug('write_sig: %s' % str(write_sig))
    # write classification
    classification_array[
        (classification_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
    ] = output_no_data
    write_class = raster_vector.write_raster(
        out_class, x - ro_x, y - ro_y, classification_array, output_no_data,
        scale, offset
    )
    log.debug('write_class: %s' % str(write_class))
    # write the algorithm raster
    if out_alg is not None:
        previous_array[
            (classification_array == cfg.nodata_val_Int32) | (nodata_mask == 1)
        ] = output_no_data
        write_alg = raster_vector.write_raster(
            out_alg, x - ro_x, y - ro_y, previous_array, output_no_data, scale,
            offset
        )
        log.debug('write_alg: %s' % str(write_alg))
    log.debug(
        'classification_array.shape: %s' % str(classification_array.shape)
    )
    return [True, out_class]


# calculation of spectral distance
def spectral_distance(*argv):
    # array variable name as defined in cfg.array_function_placeholder
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    # number of bands
    function_argument = argv[7]
    # algorithm name
    function_variable = argv[8][0]
    threshold = argv[8][1]
    log = cfg.logger.log
    log.debug(
        'function_argument: %s; function_variable: %s'
        % (str(function_argument), str(function_variable))
    )
    a = _array_function_placeholder[::, ::, :function_argument]
    b = _array_function_placeholder[::, ::, function_argument:]
    if function_variable.lower() == cfg.minimum_distance_a:
        # Euclidean distance
        _o = np.sqrt(((a - b) ** 2).sum(axis=2))
    else:
        # spectral angle
        _o = np.arccos(
            (a * b).sum(axis=2) /
            np.sqrt((a ** 2).sum(axis=2) * (b ** 2).sum(axis=2))
        ) * 180 / np.pi
    if threshold is not None:
        _o = _o > threshold
    # check nodata
    log.debug(
        '_o: %s; nodata_mask: %s' % (str(_o.shape), str(nodata_mask.shape))
    )
    if nodata_mask is not None:
        _o[nodata_mask == 1] = output_no_data
    return [[_o, None], None]


# classification through scikit-learn model
def classification_scikit(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    classifier = argv[7][cfg.model_classifier_framework]
    log = cfg.logger.log
    log.debug('classifier: %s' % str(classifier.classes_))
    normalization = argv[7][cfg.normalization_values_framework]
    function_variable_list = argv[8]
    x_min_piece, y_min_piece = argv[10]
    threshold = function_variable_list[1]
    out_class = argv[12]
    out_alg = argv[13]
    x_array = None
    if normalization[0] is not None:
        for n in range(0, _array_function_placeholder.shape[2]):
            _array_function_placeholder[::, ::, n] = eval(normalization[0][n])
    for n in range(_array_function_placeholder.shape[2]):
        # replace nodata
        _array_function_placeholder[::, ::, n][
            nodata_mask == 1] = cfg.nodata_val
        if x_array is None:
            x_array = _array_function_placeholder[::, ::, n].ravel()
        else:
            x_array = np.vstack(
                [x_array, _array_function_placeholder[::, ::, n].ravel()]
            )
    # replace nan
    x_array[np.isnan(x_array)] = cfg.nodata_val
    # prediction
    if not threshold and out_alg is None:
        _prediction = classifier.predict(x_array.T)
        classification_array = _prediction.reshape(
            _array_function_placeholder.shape[0],
            _array_function_placeholder.shape[1]
        )
        _prediction = None
        # write classification
        classification_array[nodata_mask == 1] = output_no_data
        try:
            write_class = raster_vector.write_raster(
                out_class, x - x_min_piece, y - y_min_piece,
                classification_array, output_no_data, scale, offset
            )
            log.debug(
                'write_class: %s; classification_array.shape: %s'
                % (str(write_class), str(classification_array.shape))
            )
        except Exception as err:
            log.debug(
                'classification_array.shape: %s; x: %s; y: %s: '
                % (str(classification_array.shape), str(x), str(y))
            )
            log.error(str(err))
    # write the probability raster
    elif out_alg is not None:
        try:
            _prediction_proba = classifier.predict_proba(x_array.T)
            prediction_proba_array = np.max(_prediction_proba, axis=1).reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
            classification_argmax = np.argmax(
                _prediction_proba, axis=1
            ).reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
            _prediction_proba = None
            classes = classifier.classes_
            classification_array = np.zeros_like(classification_argmax)
            for c, class_c in enumerate(classes):
                classification_array = np.where(
                    classification_argmax == c, class_c, classification_array
                )
            if threshold is not False:
                classification_array[
                    (prediction_proba_array < threshold) | (nodata_mask == 1)
                ] = output_no_data
            write_alg = raster_vector.write_raster(
                out_alg, x - x_min_piece, y - y_min_piece,
                prediction_proba_array, output_no_data, scale, offset
            )
            log.debug('write_alg: %s' % str(write_alg))
        except Exception as err:
            log.error(str(err))
            _prediction = classifier.predict(x_array.T)
            classification_array = _prediction.reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
            _prediction = None
        # write classification
        classification_array[nodata_mask == 1] = output_no_data
        write_class = raster_vector.write_raster(
            out_class, x - x_min_piece, y - y_min_piece, classification_array,
            output_no_data, scale, offset
        )
        log.debug(
            'write_class: %s; classification_array.shape: %s'
            % (str(write_class), str(classification_array.shape))
        )
    return [True, out_class]


# classification through pytorch model
def classification_pytorch(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    classifier = argv[7][cfg.model_classifier_framework]
    normalization = argv[7][cfg.normalization_values_framework]
    function_variable_list = argv[8]
    x_min_piece, y_min_piece = argv[10]
    threshold = function_variable_list[1]
    out_class = argv[12]
    out_alg = argv[13]
    x_array = None
    log = cfg.logger.log
    if normalization[0] is not None:
        for n in range(0, _array_function_placeholder.shape[2]):
            _array_function_placeholder[::, ::, n] = eval(normalization[0][n])
    for n in range(_array_function_placeholder.shape[2]):
        # replace nodata
        _array_function_placeholder[::, ::, n][
            nodata_mask == 1] = cfg.nodata_val
        if x_array is None:
            x_array = _array_function_placeholder[::, ::, n].ravel()
        else:
            x_array = np.vstack(
                [x_array, _array_function_placeholder[::, ::, n].ravel()]
            )
    # replace nan
    x_array[np.isnan(x_array)] = cfg.nodata_val
    # prediction
    torch.set_num_threads(1)
    classifier.eval()
    data_type = eval('torch.%s' % str(x_array.dtype))
    x_array = torch.tensor(x_array.T, dtype=data_type)
    if not threshold and out_alg is None:
        _prediction = classifier(x_array).argmax(1).numpy()
        classification_array = _prediction.reshape(
            _array_function_placeholder.shape[0],
            _array_function_placeholder.shape[1]
        )
        _prediction = None
        # write classification
        classification_array[nodata_mask == 1] = output_no_data
        try:
            write_class = raster_vector.write_raster(
                out_class, x - x_min_piece, y - y_min_piece,
                classification_array, output_no_data, scale, offset
            )
            log.debug('write_class: %s' % str(write_class))
            log.debug(
                'classification_array.shape: %s' % str(
                    classification_array.shape
                )
            )
        except Exception as err:
            log.debug(
                'classification_array.shape: %s; x: %s; y: %s'
                % (str(classification_array.shape), str(x), str(y))
            )
            log.error(str(err))
    # write the probability raster
    elif out_alg is not None:
        try:
            _softmax = torch.softmax(classifier(x_array), dim=1)
            prediction_proba_array, classification_array = _softmax.topk(
                1, dim=1
            )
            _softmax = None
            prediction_proba_array = prediction_proba_array.detach().numpy(

            ).reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
            classification_array = classification_array.detach().numpy(
            ).reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
            if threshold is not False:
                classification_array[
                    prediction_proba_array < threshold] = output_no_data
            prediction_proba_array[nodata_mask == 1] = output_no_data
            write_alg = raster_vector.write_raster(
                out_alg, x - x_min_piece, y - y_min_piece,
                prediction_proba_array, output_no_data, scale, offset
            )
            log.debug('write_alg: %s' % str(write_alg))
        except Exception as err:
            log.error(str(err))
            prediction = classifier(x_array).argmax(1).numpy()
            classification_array = prediction.reshape(
                _array_function_placeholder.shape[0],
                _array_function_placeholder.shape[1]
            )
        # write classification
        classification_array[nodata_mask == 1] = output_no_data
        write_class = raster_vector.write_raster(
            out_class, x - x_min_piece, y - y_min_piece, classification_array,
            output_no_data, scale, offset
        )
        log.debug(
            'write_class: %s; classification_array.shape: %s'
            % (str(write_class), str(classification_array.shape))
        )
    return [True, out_class]


# classification through pytorch pretrained model
def classification_pytorch_pretrained(*argv):
    _array_function_placeholder = argv[1][0]
    model_path = argv[7][cfg.model_path_framework]
    algorithm_name = argv[7][cfg.algorithm_name_framework]
    if (
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base or
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base_a
    ):
        model_variant = cfg.variant_base
    elif (
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_tiny or
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_tiny_a
    ):
        model_variant = cfg.variant_tiny
    else:
        model_variant = None
    classification_algorithm = argv[7][cfg.additional_algorithm_framework]
    embeddings = pretrained_pytorch_model_swin2(
        array_dic={0: _array_function_placeholder}, weights_path=model_path,
        variant=model_variant,
        band_number=_array_function_placeholder.shape[2], stack=False)
    new_args = list(argv)
    new_args[1][0] = embeddings[0]
    return classification_algorithm(*new_args)


# segmentation through pytorch pretrained model
def segmentation_pytorch_pretrained(*argv):
    scale = argv[0][0]
    offset = argv[0][1]
    output_no_data = argv[0][2]
    _array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    x = argv[4]
    y = argv[5]
    model_path = argv[7][cfg.model_path_framework]
    algorithm_name = argv[7][cfg.algorithm_name_framework]
    pretrained_model_replace = argv[7][cfg.model_reclass_framework]
    num_classes = argv[7][cfg.num_classes_framework]
    n_processes = argv[7][cfg.n_processes_framework]
    x_min_piece, y_min_piece = argv[10]
    out_class = argv[12]
    log = cfg.logger.log
    if (
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base_seg
            or
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base_seg_a
            or
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base_rgb_seg
            or
            algorithm_name == cfg.pytorch_pretrained_s2_swin_v2_base_rgb_seg_a
    ):
        model_variant = cfg.variant_base
    else:
        model_variant = None
    segmentation = segmentation_pytorch_model_swin2(
        array_dic={0: _array_function_placeholder}, weights_path=model_path,
        variant=model_variant, num_classes=num_classes,
        band_number=_array_function_placeholder.shape[2], stack=False,
        replace_keys=pretrained_model_replace, n_processes=n_processes
    )
    # write classification
    classification_array = segmentation[0]
    classification_array[nodata_mask == 1] = output_no_data
    write_class = raster_vector.write_raster(
        out_class, x - x_min_piece, y - y_min_piece, classification_array,
        output_no_data, scale, offset
    )
    log.debug(
        'write_class: %s; classification_array.shape: %s'
        % (str(write_class), str(classification_array.shape))
    )
    return [True, out_class]












# calculate raster unique values with sum
def raster_unique_values_with_sum(*argv):
    log = cfg.logger.log
    log.debug('start')
    raster_array_band = argv[1][0]
    try:
        nodata_mask = argv[2]
        b = raster_array_band[nodata_mask != 1]
        stats = np.array(np.unique(b[~np.isnan(b)], return_counts=True))
    except Exception as err:
        stats = np.array(
            np.unique(
                raster_array_band[~np.isnan(raster_array_band)],
                return_counts=True
            )
        )
        log.error(str(err))
    log.debug('end')
    return [None, stats]


















# calculate spectral signature
def spectral_signature(*argv):
    # noinspection PyPackageRequirements
    from osgeo import gdal
    log = cfg.logger.log
    log.debug('start')
    array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    # vector path
    function_argument = argv[7]
    # reference path
    function_variable = argv[8]
    temp = cfg.temp.temporary_mem_path(name_suffix=cfg.tif_suffix)
    raster_vector.vector_to_raster(
        vector_path=function_argument, burn_values=1, output_path=temp,
        reference_raster_path=function_variable, extent=True
    )
    _a = raster_vector.read_raster(temp)
    gdal.Unlink(temp)
    _a[nodata_mask == 1] = np.nan
    array_roi = array_function_placeholder[_a == 1]
    mean = np.nanmean(array_roi)
    std = np.nanstd(array_roi)
    count = np.count_nonzero(_a == 1)
    log.debug('end')
    return [None, [mean, std, count]]


# get raster band values for scatter plot
def get_values_for_scatter_plot(*argv):
    # noinspection PyPackageRequirements
    from osgeo import gdal
    log = cfg.logger.log
    log.debug('start')
    array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    # vector path
    function_argument = argv[7]
    # reference path
    function_variable = argv[8]
    temp = cfg.temp.temporary_mem_path(name_suffix=cfg.tif_suffix)
    raster_vector.vector_to_raster(
        vector_path=function_argument, burn_values=1, output_path=temp,
        reference_raster_path=function_variable, extent=True
    )
    _a = raster_vector.read_raster(temp)
    gdal.Unlink(temp)
    _a[nodata_mask == 1] = np.nan
    array_roi = array_function_placeholder[_a == 1]
    log.debug('end')
    return [None, array_roi.ravel()]


# calculate region growing from seed value
def region_growing(*argv):
    log = cfg.logger.log
    log.debug('start')
    array_function_placeholder = argv[1][0]
    nodata_mask = argv[2]
    # roi parameters
    function_variable = argv[8]
    array_roi = array_function_placeholder
    array_roi[nodata_mask == 1] = np.nan
    seed_x = function_variable[0]
    seed_y = function_variable[1]
    max_spectral_distance = function_variable[2]
    minimum_size = function_variable[3]
    seed_array = np.zeros(array_roi.shape)
    seed_value = float(array_roi[seed_y, seed_x].item())
    log.debug('array_roi.shape: %s; seed_value: %s'
              % (str(array_roi.shape), str(seed_value)))
    # if nodata
    if np.isnan(seed_value):
        return seed_array
    seed_array.fill(seed_value)
    difference_array = abs(array_roi - seed_value)
    # calculate minimum difference
    unique_difference_array = np.unique(difference_array)
    unique_difference_distance = unique_difference_array[
        unique_difference_array > float(max_spectral_distance)]
    unique_difference_array = np.insert(
        unique_difference_distance, 0, float(max_spectral_distance)
    )
    region = None
    region_seed_value = None
    region_value_mask = seed_array
    for i in unique_difference_array:
        region_label, num_features = label(difference_array <= i)
        # value of ROI seed
        # noinspection PyUnresolvedReferences
        region_seed_value = region_label[seed_y, seed_x]
        region_value_mask = (region_label == region_seed_value)
        if (region_seed_value != 0
                and np.count_nonzero(region_value_mask) >= minimum_size):
            region = np.copy(region_value_mask)
            break
    if region is None and region_seed_value != 0:
        region = np.copy(region_value_mask)
    log.debug('end')
    return [None, region]


# get band arrays
def get_band_arrays(
        process, progress_queue, argument_list, logger, temp
):
    cfg.logger = logger
    cfg.temp = temp
    results = []
    errors = False
    for n, d in enumerate(argument_list, start=1):
        try:
            # iterate signatures
            array_dict = {}
            # optional calc data type, if None use input data type
            calc_data_type = d['calc_data_type']
            if 'field_name' in d:
                field_name = d['field_name']
            else:
                field_name = str(cfg.uid_field_name)
            for s in d['signature_id_list']:
                r_arr_v_arr_list = []
                nd_bool_list = []
                ravel_list = []
                # iterate rasters
                for v in d['virtual_path_list']:
                    extract = raster_vector.extract_vector_to_raster(
                        vector_path=d['roi_path'],
                        reference_raster_path=v, calc_data_type=calc_data_type,
                        available_ram=d['available_ram'],
                        attribute_filter="%s = '%s'" % (field_name, str(s)),
                        ravel=d['ravel'], buffer=d['buffer']
                    )
                    if extract is False:
                        return [None, 'error extract', str(process)]
                    # get raster array and signature raster array
                    if extract[0] is not None:
                        r_arr_v_arr_list.append([extract[0], extract[1]])
                        # get raster nodata array
                        nd_bool_list.append(extract[2])
                        ravel_list.append(d['ravel'])
                # create nodata array for all rasters
                nd_array = None
                for nd_bool in nd_bool_list:
                    if nd_array is None:
                        nd_array = nd_bool
                    else:
                        nd_array = nd_array * nd_bool
                # create array list
                array_list = []
                _vector_raster = None
                for r, i in enumerate(r_arr_v_arr_list):
                    if ravel_list[r]:
                        _a = i[0][nd_array]
                        _b = i[1][nd_array]
                        array_list.append(_a[_b == 1])
                    else:
                        _a = i[0] * nd_array
                        _vector_raster = i[1] * nd_array
                        array_list.append(_a)
                # calculate numpy functions
                if d.get('numpy_functions') is not None:
                    result_dict = {}
                    for f in d['numpy_functions']:
                        for _ in array_list:
                            result_dict[f] = eval(d['numpy_functions'][f])
                    array_dict[s] = result_dict
                # functions such as pretrained_pytorch_model_swin2
                elif d.get('function') is not None:
                    fun = eval(d['function'][0])
                    weights_path = d['function'][1]
                    model_variant = d['function'][2]
                    pytorch_device = d['pytorch_device']
                    array_dict[s] = fun({0: array_list}, weights_path,
                                        len(array_list), model_variant,
                                        {0: _vector_raster}, pytorch_device)
                else:
                    array_dict[s] = array_list
            results.append(array_dict)
            if progress_queue is not None and progress_queue.empty():
                progress_queue.put([n, len(argument_list)], False)
        except Exception as err:
            errors = str(err)
    return [results, errors, str(process)]


# fit
def fit_classifier(*argv):
    p, temp, ram, log_process, cfg.logger = argv[0]
    classifier_list = argv[1]
    arg_dict_list = argv[2]
    result = []
    for i, value in enumerate(arg_dict_list):
        classifier = classifier_list[i]
        if log_process and log_process is not None:
            with open('%s/scikit' % temp.dir, 'w') as f:
                with redirect_stdout(f):
                    classifier.fit(**value)
        else:
            # set verbose
            try:
                classifier.verbose = 0
            except Exception as err:
                str(err)
            classifier.fit(**arg_dict_list[i])
        classifier.verbose = 0
        result.append(classifier)
    return [result, False, None]


# score
def score_classifier(*argv):
    p, temp, ram, log_process, cfg.logger = argv[0]
    classifier_list = argv[1]
    arg_dict_list = argv[2]
    result = []
    for i, value in enumerate(arg_dict_list):
        classifier = classifier_list[i]
        if log_process and log_process is not None:
            with open('%s/scikit' % temp.dir, 'w') as f:
                with redirect_stdout(f):
                    score = classifier.score(**value)
        else:
            # set verbose
            try:
                classifier.verbose = 0
            except Exception as err:
                str(err)
            score = classifier.score(**arg_dict_list[i])
        result.append(score)
    return [result, False, None]


# score classifier with stratified k fold
def score_classifier_stratified(
        process, progress_queue, argument_list, logger, temp
):
    cfg.logger = logger
    cfg.temp = temp
    results = []
    errors = False
    for n, d in enumerate(argument_list, start=1):
        try:
            # calculate score by cross-validation with stratification
            scores = cross_val_score(
                d['classifier'], d['x_matrix'], d['y'],
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
            )
            score = np.array(scores)
            results.append([d['classifier'], score.mean(), score.std()])
            if progress_queue is not None and progress_queue.empty():
                progress_queue.put([n, len(argument_list)], False)
        except Exception as err:
            errors = str(err)
    return [results, errors, str(process)]


# clip_raster
def clip_raster(
        process, progress_queue, argument_list, logger, temp
):
    cfg.logger = logger
    log = cfg.logger.log
    cfg.temp = temp
    results = []
    errors = False
    for n, d in enumerate(argument_list, start=1):
        gdal_path = d['gdal_path']
        log.debug('start')
        if gdal_path is not None:
            for path in gdal_path.split(';'):
                try:
                    os.add_dll_directory(path)
                    cfg.gdal_path = path
                except Exception as err:
                    str(err)
        # noinspection PyPackageRequirements
        from osgeo import gdal, ogr, osr
        # GDAL config
        try:
            memory = str(int(d['available_ram']) * 1000000)
            gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'TRUE')
            gdal.SetConfigOption('GDAL_CACHEMAX', str(memory))
            gdal.SetConfigOption('VSI_CACHE', 'FALSE')
            gdal.SetConfigOption('CHECK_DISK_FREE_SPACE', 'FALSE')
            gdal.SetConfigOption('GTIFF_SRS_SOURCE', 'EPSG')
            gdal.DontUseExceptions()
        except Exception as err:
            str(err)
        try:
            _r_d = gdal.Open(d['input_raster'], gdal.GA_ReadOnly)
            input_band = _r_d.GetRasterBand(1)
            no_data = input_band.GetNoDataValue()
            sr = osr.SpatialReference()
            sr.ImportFromWkt(_r_d.GetProjectionRef())
            if d['extent_list'] is not None:
                # copy raster band
                op = ' -co BIGTIFF=YES -co COMPRESS=%s' % d['compress_format']
                op += ' -of %s' % 'GTiff'
                if no_data is not None:
                    op += ' -srcnodata %s -dstnodata %s' % (no_data, no_data)
                to = gdal.WarpOptions(gdal.ParseCommandLine(op))
            else:
                cutline = d['vector_path']
                _vector = ogr.Open(cutline)
                _v_layer = _vector.GetLayer()
                v_sr = _v_layer.GetSpatialRef()
                if sr.IsSame(v_sr) != 1:
                    _v_layer = None
                    _vector = None
                    # create temp vector
                    cutline = cfg.temp.temporary_mem_path(
                        name_suffix=cfg.gpkg_suffix
                    )
                    gdal.VectorTranslate(
                        cutline, d['vector_path'], format='GPKG',
                        dstSRS=sr.ExportToWkt(),
                    )
                    _vector = ogr.Open(cutline)
                    _v_layer = _vector.GetLayer()
                extent = _v_layer.GetExtent()
                _v_layer = None
                _vector = None
                crop = True
                op = ' -co BIGTIFF=YES -co COMPRESS=%s' % d['compress_format']
                # op += ' -wo CUTLINE_ALL_TOUCHED = TRUE'
                to = gdal.WarpOptions(
                    gdal.ParseCommandLine(op),
                    format='GTiff', outputBounds=extent,
                    dstSRS=sr.ExportToWkt(), cutlineDSName=cutline,
                    cropToCutline=crop, cutlineWhere=d['where'],
                    srcNodata=no_data, dstNodata=no_data
                )
                if sr.IsSame(v_sr) != 1:
                    gdal.Unlink(cutline)
            gdal.Warp(d['output'], d['input_raster'], options=to)
            _r_d = None
            results.append([d['output']])
            if progress_queue is not None and progress_queue.empty():
                progress_queue.put([n, len(argument_list)], False)
        except Exception as err:
            errors = str(err)
    return [results, errors, str(process)]










# edit raster
# noinspection PyShadowingBuiltins
def edit_raster(
        process, progress_queue, argument_list, logger, temp
):
    cfg.logger = logger
    log = cfg.logger.log
    cfg.temp = temp
    results = []
    errors = False
    for n, d in enumerate(argument_list, start=1):
        gdal_path = d['gdal_path']
        log.debug('start')
        if gdal_path is not None:
            for path in gdal_path.split(';'):
                try:
                    os.add_dll_directory(path)
                    cfg.gdal_path = path
                except Exception as err:
                    str(err)
        # noinspection PyPackageRequirements
        from osgeo import gdal
        # GDAL config
        try:
            memory = str(int(d['available_ram']) * 1000000)
            gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'TRUE')
            gdal.SetConfigOption('GDAL_CACHEMAX', str(memory))
            gdal.SetConfigOption('VSI_CACHE', 'FALSE')
            gdal.SetConfigOption('CHECK_DISK_FREE_SPACE', 'FALSE')
            gdal.SetConfigOption('GTIFF_SRS_SOURCE', 'EPSG')
            gdal.DontUseExceptions()
        except Exception as err:
            str(err)
        try:
            raster = d['old_array']
            if raster is not None:
                _r_column_start = d['column_start']
                _r_row_start = d['row_start']
                # write raster
                raster_vector.write_raster(
                    d['input_raster'], _r_column_start, _r_row_start, raster
                )
                results.append(None)
                results.append(None)
                results.append(None)
            else:
                constant_value = d['constant_value']
                expression = d['expression']
                _r_d = gdal.Open(d['input_raster'], gdal.GA_Update)
                _v_d = gdal.Open(d['vector_raster'], gdal.GA_ReadOnly)
                # get pixel size and top left
                _r_d_gt = _r_d.GetGeoTransform()
                _r_left = _r_d_gt[0]
                _r_top = _r_d_gt[3]
                r_p_x_size = _r_d_gt[1]
                r_p_y_size = _r_d_gt[5]
                _v_d_gt = _v_d.GetGeoTransform()
                _v_left = _v_d_gt[0]
                _v_top = _v_d_gt[3]
                # get pixel columns
                _r_x_size = _r_d.RasterXSize
                _v_x_size = _v_d.RasterXSize
                # get pixel rows
                _r_y_size = _r_d.RasterYSize
                _v_y_size = _v_d.RasterYSize
                if _v_left < _r_left:
                    orig_x = _r_left
                else:
                    orig_x = _v_left
                if _v_top > _r_top:
                    orig_y = _r_top
                else:
                    orig_y = _v_top
                _r_column_start = abs(int((_r_left - orig_x) / r_p_x_size))
                _r_row_start = abs(int((_r_top - orig_y) / r_p_y_size))
                _v_column_start = abs(int((_v_left - orig_x) / r_p_x_size))
                _v_row_start = abs(int((_v_top - orig_y) / r_p_y_size))
                columns = _v_x_size - _v_column_start
                rows = _v_y_size - _v_row_start
                if columns < 1 or rows < 1:
                    raise 'not enough pixels'
                if _r_column_start + columns > _r_x_size:
                    r_column = _r_x_size - _r_column_start
                else:
                    r_column = columns
                if r_column < 0:
                    raise 'outside raster'
                if _r_row_start + rows > _r_y_size:
                    r_rows = _r_y_size - _r_row_start
                else:
                    r_rows = rows
                if r_rows < 0:
                    raise 'outside raster'
                # get raster band
                _r_band = _r_d.GetRasterBand(1)
                try:
                    _r_offset = _r_band.GetOffset()
                    _r_scale = _r_band.GetScale()
                    if _r_offset is None:
                        _r_offset = 0
                    if _r_scale is None:
                        _r_scale = 1
                except Exception as err:
                    str(err)
                    _r_offset = 0
                    _r_scale = 1
                # set variable name as cfg.variable_raster_name
                o_raster = _r_band.ReadAsArray(
                    _r_column_start, _r_row_start, r_column, r_rows
                )
                raster = o_raster * _r_scale + _r_offset
                # get vector raster band
                _v_band = _v_d.GetRasterBand(1)
                try:
                    _v_offset = _v_band.GetOffset()
                    _v_scale = _v_band.GetScale()
                    if _v_offset is None:
                        _v_offset = 0
                    if _v_scale is None:
                        _v_scale = 1
                except Exception as err:
                    str(err)
                    _v_offset = 0
                    _v_scale = 1
                _v_band = _v_band.ReadAsArray(
                    _v_column_start, _v_row_start, r_column, r_rows
                )
                # set variable name as cfg.variable_vector_name
                vector = _v_band * _v_scale + _v_offset
                # expression
                if expression is not None:
                    # expose numpy functions
                    namespace = {
                        'raster': raster, 'vector': vector,
                        'np': np, 'log': np.log, 'log10': np.log10,
                        'sqrt': np.sqrt, 'cos': np.cos, 'arccos': np.arccos,
                        'sin': np.sin, 'arcsin': np.arcsin, 'tan': np.tan,
                        'arctan': np.arctan, 'exp': np.exp, 'min': np.nanmin,
                        'max': np.nanmax, 'sum': np.nansum,
                        'percentile': np.nanpercentile, 'median': np.nanmedian,
                        'mean': np.nanmean, 'std': np.nanstd,
                        'where': np.where, 'nan': np.nan
                    }
                    data_array = eval(expression, {'__builtins__': None},
                                      namespace)
                else:
                    data_array = np.where(vector > 0, constant_value, raster)
                _r_band = _v_band = None
                _r_d = _v_d = None
                # write raster
                raster_vector.write_raster(
                    d['input_raster'], _r_column_start, _r_row_start,
                    data_array / _r_scale - _r_offset
                )
                results.append(o_raster)
                results.append(_r_column_start)
                results.append(_r_row_start)
            if progress_queue is not None and progress_queue.empty():
                progress_queue.put([n, len(argument_list)], False)
        except Exception as err:
            errors = str(err)
    return [results, errors, str(process)]




