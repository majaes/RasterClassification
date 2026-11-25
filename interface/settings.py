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

import sys
from shutil import copy

from qgis.PyQt.QtCore import QDir
from qgis.PyQt.QtWidgets import QApplication

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])




































    #cfg.qgis_registry[cfg.reg_smtp_pass] = ''










""" Tests """


# test required dependencies
# noinspection PyTypeChecker
def test_all_dependencies():
    text = []
    if not test_numpy():
        text.append('NumPy')
    if not test_scipy():
        text.append('SciPy')
    if not test_matplotlib():
        text.append('Matplotlib')
    if not test_gdal():
        text.append('GDAL')
    if not test_pytorch():
        text.append('PyTorch')
    if not test_torchvision():
        text.append('Torchvision')
    if not test_sklearn():
        text.append('scikit-learn')
    if not test_remotior_sensus():
        text.append('Remotior Sensus')
    if len(text) > 0:
        message =  QApplication.translate(
            'semiautomaticclassificationplugin',
            'Failed to load the following dependencies'
        ) + ': ' + ', '.join(text)
    else:
        message = QApplication.translate(
            'semiautomaticclassificationplugin', 'Dependencies checked'
        )
    return message




# test Remotior Sensus
def test_remotior_sensus():
    test = True
    try:
        import remotior_sensus
    except Exception as err:
        str(err)
        test = False
    return test




# test GDAL
def test_gdal():
    test = True
    try:
        from osgeo import gdal, ogr, osr
        assert gdal.Translate
    except Exception as err:
        str(err)
        test = False
    return test


# test PyTorch
def test_pytorch():
    test = True
    try:
        # noinspection PyUnresolvedReferences
        import torch
    except Exception as err:
        str(err)
        test = False
    return test


# test Torchvision
def test_torchvision():
    test = True
    try:
        # noinspection PyUnresolvedReferences
        from torchvision.models import swin_v2_b
    except Exception as err:
        str(err)
        test = False
    return test


# test scikit-learn
def test_sklearn():
    test = True
    try:
        from sklearn import svm
    except Exception as err:
        str(err)
        test = False
    return test




# test Numpy
def test_numpy():
    test = True
    try:
        import numpy
        numpy.count_nonzero([1, 1, 0])
    except Exception as err:
        str(err)
        test = False
    return test


# test Scipy
def test_scipy():
    test = True
    try:
        import scipy
    except Exception as err:
        str(err)
        test = False
    return test


# test Matplotlib
def test_matplotlib():
    test = True
    try:
        from matplotlib.ticker import MaxNLocator
    except Exception as err:
        str(err)
        test = False
    return test
