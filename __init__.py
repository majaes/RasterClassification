# RasterClassification
# The Semi-Automatic Classification Plugin for QGIS allows for the supervised 
# classification of remote sensing images, providing tools for the download, 
# the preprocessing and postprocessing of images.
# begin: 2012-12-29
# Copyright (C) 2012-2026 by Luca Congedo.
# Author: Luca Congedo
# Email: ing.congedoluca@gmail.com
#
# This file is part of RasterClassification.
# RasterClassification is free software: you can redistribute it 
# and/or modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation, 
# either version 3 of the License, or (at your option) any later version.
# RasterClassification is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with RasterClassification. 
# If not, see <https://www.gnu.org/licenses/>.


def name():
    return 'Raster Classification'


def description():
    return (
        'Raster Classification: supervised classification of remote sensing '
        'images, with tools for the download, preprocessing and '
        'postprocessing of images.'
    )


def version():
    return 'Version 1.0.0'


def icon():
    return 'raster_classification.png'


# noinspection PyPep8Naming
def qgisMinimumVersion():
    return '3.34'


def author():
    return 'ANABA MANGA'


def email():
    return 'majaesabana@gmail.com'


def category():
    return 'Raster'


# noinspection PyPep8Naming
def classFactory(iface):
    from .raster_classification import (
        RasterClassification
    )
    return RasterClassification(iface)


def homepage():
    return (
        'https://anbmng.com')


def tracker():
    return (
        'https://github.com/majaes/RasterClassification'
        '/issues')


def repository():
    return (
        'https://github.com/majaes/RasterClassification'
    )
