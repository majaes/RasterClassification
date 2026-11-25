# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Predefined color compositions and spectral indices.

A preset picks the bands of the active band set by their center wavelength
(or, for Sentinel-2 files, by the band name such as B04 or B8A), so the user
does not need to count band positions.
"""

import os
import re
import time

from PyQt6.QtWidgets import QComboBox, QApplication
from qgis.core import (
    Qgis, QgsRasterLayer, QgsStyle, QgsColorRampShader, QgsRasterShader,
    QgsSingleBandPseudoColorRenderer, QgsProject
)
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry

from ..core import config as cfg

# spectral roles: (center wavelength in micrometers, tolerance)
ROLES = {
    'blue': (0.485, 0.04),
    'green': (0.560, 0.04),
    'red': (0.660, 0.04),
    'nir': (0.850, 0.05),
    'swir1': (1.610, 0.12),
    'swir2': (2.200, 0.15),
}
# Sentinel-2 band names for each role (used when wavelengths are missing)
S2_NAMES = {
    'blue': ('B02',), 'green': ('B03',), 'red': ('B04',),
    'nir': ('B08', 'B8A'), 'swir1': ('B11',), 'swir2': ('B12',),
}

# color composites: (label, (red, green, blue))
COMPOSITES = [
    ('Natural color (true color)', ('red', 'green', 'blue')),
    ('Color infrared (vegetation in red)', ('nir', 'red', 'green')),
    ('Agriculture', ('swir1', 'nir', 'blue')),
    ('Healthy vegetation', ('nir', 'swir1', 'blue')),
    ('Short-wave infrared', ('swir2', 'nir', 'red')),
    ('Urban', ('swir2', 'swir1', 'red')),
    ('Geology', ('swir2', 'swir1', 'blue')),
]
# spectral indices: (label, formula with two roles, min, max, ramp name)
INDICES = [
    ('NDVI - vegetation', ('nir', 'red'), -0.2, 0.9, 'RdYlGn'),
    ('NDWI - water', ('green', 'nir'), -0.8, 0.8, 'RdYlBu'),
    ('NDBI - built-up', ('swir1', 'nir'), -0.8, 0.5, 'Spectral'),
    ('NBR - burned areas', ('nir', 'swir2'), -0.5, 0.9, 'RdYlGn'),
]
TITLE = 'Predefined compositions'


def _wavelength_um(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    # nanometers to micrometers
    return value / 1000 if value > 50 else value


def find_band(bandset_x, role):
    """ Return the band number of the band that best matches the role. """
    center, tolerance = ROLES[role]
    best = None
    best_distance = None
    for band in bandset_x.bands:
        wavelength = _wavelength_um(band['wavelength'])
        if wavelength is None:
            continue
        distance = abs(wavelength - center)
        if distance <= tolerance and (
                best_distance is None or distance < best_distance):
            best, best_distance = int(band['band_number']), distance
    if best is not None:
        return best
    # fallback: Sentinel-2 band name
    for name in S2_NAMES[role]:
        pattern = re.compile(r'(^|[_\W])%s(\W|_|$)' % name, re.IGNORECASE)
        for band in bandset_x.bands:
            if pattern.search(str(band['name'])):
                return int(band['band_number'])
    return None


def _message(text, level=Qgis.MessageLevel.Warning):
    cfg.iface.messageBar().pushMessage(
        'Raster Classification', text, level=level, duration=8
    )


def _active_bandset():
    number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get_bandset_by_number(number)
    if bandset_x is None or bandset_x.get_band_count() == 0:
        _message(QApplication.translate(
            'semiautomaticclassificationplugin',
            'Add bands to the band set first (Open file or Add layer).'
        ))
        return None, number
    return bandset_x, number


def apply_composite(roles):
    bandset_x, number = _active_bandset()
    if bandset_x is None:
        return False
    numbers = [find_band(bandset_x, r) for r in roles]
    missing = [r for r, n in zip(roles, numbers) if n is None]
    if missing:
        _message(
            'Bands not found in the band set for: %s. Set the satellite in '
            'the Wavelength menu, or add the missing bands.'
            % ', '.join(m.upper() for m in missing)
        )
        return False
    return cfg.utils.set_rgb_color_composite(
        '%s-%s-%s' % tuple(numbers), number
    )


def apply_index(label, roles, minimum, maximum, ramp_name):
    bandset_x, number = _active_bandset()
    if bandset_x is None:
        return False
    first = find_band(bandset_x, roles[0])
    second = find_band(bandset_x, roles[1])
    if first is None or second is None:
        _message(
            'Bands not found in the band set for %s (needs %s and %s). Set '
            'the satellite in the Wavelength menu, or add the missing bands.'
            % (label.split(' ')[0], roles[0].upper(), roles[1].upper())
        )
        return False
    entries = []
    layers = []
    for ref, band_number in (('a', first), ('b', second)):
        layer = QgsRasterLayer(bandset_x.get_absolute_path(band_number))
        if not layer.isValid():
            _message('Unable to open band %s' % band_number)
            return False
        layers.append(layer)
        entry = QgsRasterCalculatorEntry()
        entry.ref = '%s@1' % ref
        entry.raster = layer
        entry.bandNumber = 1
        entries.append(entry)
    # use the grid of the finer band for the result
    base = min(layers, key=lambda x: x.rasterUnitsPerPixelX())
    name = label.split(' ')[0]
    output = os.path.join(
        cfg.temp_dir, '%s_%s.tif' % (name, time.strftime('%Y%m%d_%H%M%S'))
    )
    calc = QgsRasterCalculator(
        '("a@1" - "b@1") / ("a@1" + "b@1")', output, 'GTiff', base.extent(),
        base.crs(), base.width(), base.height(), entries,
        QgsProject.instance().transformContext()
    )
    if calc.processCalculation() != 0:
        _message('Unable to calculate %s' % name)
        return False
    result = QgsRasterLayer(output, '%s %s' % (name, number))
    if not result.isValid():
        _message('Unable to open the %s result' % name)
        return False
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    shader = QgsColorRampShader(minimum, maximum, ramp)
    shader.classifyColorRamp(7)
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader)
    result.setRenderer(QgsSingleBandPseudoColorRenderer(
        result.dataProvider(), 1, raster_shader
    ))
    QgsProject.instance().addMapLayer(result)
    _message('%s calculated: %s' % (name, output), Qgis.MessageLevel.Info)
    return True


def preset_selected(combo):
    index = combo.currentIndex()
    if index <= 0:
        return
    n = len(COMPOSITES)
    try:
        if index <= n:
            apply_composite(COMPOSITES[index - 1][1])
        else:
            apply_index(*INDICES[index - n - 1])
    except Exception as err:
        cfg.logger.log.error(str(err))
        _message(str(err))
    finally:
        # back to the title so the same preset can be chosen again
        combo.blockSignals(True)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)


def create_combo(parent):
    combo = QComboBox(parent)
    combo.addItem(TITLE)
    for label, _roles in COMPOSITES:
        combo.addItem(label)
    for label, *_rest in INDICES:
        combo.addItem(label)
    combo.setToolTip(
        'Display a predefined color composite, or calculate a spectral '
        'index, from the bands of the band set (bands are found from the '
        'Wavelength setting or the Sentinel-2 band names)'
    )
    combo.activated.connect(lambda _i, c=combo: preset_selected(c))
    return combo
