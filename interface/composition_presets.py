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

from qgis.PyQt.QtWidgets import QComboBox
from qgis.core import (
    Qgis, QgsRasterLayer, QgsStyle, QgsColorRampShader, QgsRasterShader,
    QgsSingleBandPseudoColorRenderer, QgsProject, QgsTask, QgsFeedback,
    QgsApplication
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
ROLE_LABELS = {
    'blue': 'Blue (B02)', 'green': 'Green (B03)', 'red': 'Red (B04)',
    'nir': 'NIR (B08)', 'swir1': 'SWIR1 (B11)', 'swir2': 'SWIR2 (B12)',
}

# every preset combo created (dock, toolbar)
COMBOS = []

# color composites: (label, (red, green, blue)); the first is the default
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


def _active_bandset(quiet=False):
    number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get_bandset_by_number(number)
    if bandset_x is None or bandset_x.get_band_count() == 0:
        if not quiet:
            _message('Add bands to the band set first (Open file or '
                     'Add layer).')
        return None, number
    return bandset_x, number


def missing_roles(bandset_x, roles):
    """ Labels of the roles without a matching band in the band set. """
    if bandset_x is None:
        return [ROLE_LABELS[r] for r in roles]
    return [ROLE_LABELS[r] for r in roles if find_band(bandset_x, r) is None]


def _missing_message(name, missing):
    return '%s needs the band(s): %s. Add them to the band set.' % (
        name, ', '.join(missing))


def apply_composite(roles, name='This composition', quiet=False):
    bandset_x, number = _active_bandset(quiet)
    if bandset_x is None:
        return False
    missing = missing_roles(bandset_x, roles)
    if missing:
        if not quiet:
            _message(_missing_message(name, missing))
        return False
    numbers = [find_band(bandset_x, r) for r in roles]
    result = bool(cfg.utils.set_rgb_color_composite(
        '%s-%s-%s' % tuple(numbers), number
    ))
    if result:
        hide_index_layers()
    return result


def apply_default():
    """ Display the natural color composite of a new band set; when the
    bands are not recognized, the first three bands are used. """
    if not apply_composite(COMPOSITES[0][1], quiet=True):
        number = cfg.project_registry[cfg.reg_active_bandset_number]
        cfg.utils.set_rgb_color_composite('3-2-1', number)
    for combo in COMBOS:
        combo.blockSignals(True)
        combo.setCurrentIndex(0)
        combo.setProperty('previous', 0)
        combo.setProperty('composition', 0)
        combo.blockSignals(False)


def apply_index(label, roles, minimum, maximum, ramp_name):
    bandset_x, number = _active_bandset()
    if bandset_x is None:
        return False
    name = label.split(' ')[0]
    missing = missing_roles(bandset_x, roles)
    if missing:
        _message(_missing_message(name, missing))
        return False
    first = find_band(bandset_x, roles[0])
    second = find_band(bandset_x, roles[1])
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
    output = os.path.join(
        cfg.temp_dir, '%s_%s.tif' % (name, time.strftime('%Y%m%d_%H%M%S'))
    )
    calc = QgsRasterCalculator(
        '("a@1" - "b@1") / ("a@1" + "b@1")', output, 'GTiff', base.extent(),
        base.crs(), base.width(), base.height(), entries,
        QgsProject.instance().transformContext()
    )
    # the calculation runs in the background: QGIS stays usable
    task = IndexTask(calc, layers, output, name, number, minimum, maximum,
                     ramp_name)
    TASKS.append(task)
    QgsApplication.taskManager().addTask(task)
    _message(
        'Calculating %s in the background (progress in the Tasks panel, you '
        'can keep working). The result is added to the map when finished.'
        % name, Qgis.MessageLevel.Info
    )
    return True


# running tasks (kept alive until they finish)
TASKS = []
# ids of the index layers added to the map
INDEX_LAYER_IDS = []


def hide_index_layers():
    """ Hide the index layers, so that the composition is visible. """
    root = QgsProject.instance().layerTreeRoot()
    for layer_id in list(INDEX_LAYER_IDS):
        node = root.findLayer(layer_id)
        if node is None:
            INDEX_LAYER_IDS.remove(layer_id)
        else:
            node.setItemVisibilityChecked(False)


def _combo_back_to_composition():
    for combo in COMBOS:
        composition = combo.property('composition') or 0
        combo.blockSignals(True)
        combo.setCurrentIndex(composition)
        combo.setProperty('previous', composition)
        combo.blockSignals(False)


class IndexTask(QgsTask):
    """ Calculation of a spectral index in a background task. """

    def __init__(self, calc, layers, output, name, number, minimum, maximum,
                 ramp_name):
        flag = getattr(QgsTask, 'Flag', QgsTask).CanCancel
        QgsTask.__init__(self, 'Raster Classification: %s' % name, flag)
        self.calc = calc
        # the input layers must stay alive during the calculation
        self.layers = layers
        self.output = output
        self.name = name
        self.number = number
        self.minimum = minimum
        self.maximum = maximum
        self.ramp_name = ramp_name
        self.feedback = QgsFeedback()
        self.feedback.progressChanged.connect(self.setProgress)

    def run(self):
        try:
            return self.calc.processCalculation(self.feedback) == 0
        except Exception as err:
            self.error = str(err)
            return False

    def cancel(self):
        self.feedback.cancel()
        QgsTask.cancel(self)

    def finished(self, result):
        if self in TASKS:
            TASKS.remove(self)
        self.layers = None
        if not result:
            if os.path.isfile(self.output):
                try:
                    os.remove(self.output)
                except OSError:
                    pass
            _message('%s calculation stopped.' % self.name)
            _combo_back_to_composition()
            return
        layer = QgsRasterLayer(
            self.output, '%s %s' % (self.name, self.number)
        )
        if not layer.isValid():
            _message('Unable to open the %s result' % self.name)
            _combo_back_to_composition()
            return
        ramp = QgsStyle.defaultStyle().colorRamp(self.ramp_name)
        shader = QgsColorRampShader(self.minimum, self.maximum, ramp)
        shader.classifyColorRamp(7)
        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(shader)
        layer.setRenderer(QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(), 1, raster_shader
        ))
        QgsProject.instance().addMapLayer(layer)
        INDEX_LAYER_IDS.append(layer.id())
        _message('%s calculated: %s' % (self.name, self.output),
                 Qgis.MessageLevel.Info)


class PresetCombo(QComboBox):
    """ Combo of the predefined compositions; the entries whose bands are
    not in the band set are greyed out, with the missing bands as tooltip. """

    def showPopup(self):
        try:
            bandset_x, _n = _active_bandset(quiet=True)
            model = self.model()
            n = len(COMPOSITES)
            for i in range(self.count()):
                roles = COMPOSITES[i][1] if i < n else INDICES[i - n][1]
                missing = missing_roles(bandset_x, roles)
                item = model.item(i)
                item.setEnabled(not missing)
                item.setToolTip(
                    '' if not missing else 'Missing: %s' % ', '.join(missing)
                )
        except Exception as err:
            str(err)
        QComboBox.showPopup(self)


def preset_selected(combo, previous):
    index = combo.currentIndex()
    n = len(COMPOSITES)
    ok = False
    try:
        if index < n:
            ok = apply_composite(COMPOSITES[index][1], COMPOSITES[index][0])
            if ok:
                combo.setProperty('composition', index)
        else:
            # the calculation starts in the background: the combo shows the
            # index, and goes back to the composition if it fails
            ok = apply_index(*INDICES[index - n])
    except Exception as err:
        cfg.logger.log.error(str(err))
        _message(str(err))
    if ok:
        combo.setProperty('previous', index)
    else:
        combo.blockSignals(True)
        combo.setCurrentIndex(previous)
        combo.blockSignals(False)


def create_combo(parent):
    combo = PresetCombo(parent)
    for label, _roles in COMPOSITES:
        combo.addItem(label)
    for label, *_rest in INDICES:
        combo.addItem(label)
    combo.setProperty('previous', 0)
    combo.setProperty('composition', 0)
    combo.setToolTip(
        'Color composition of the band set (default: natural color), or '
        'calculation of a spectral index. Entries that need bands missing '
        'from the band set are greyed out.'
    )
    combo.activated.connect(
        lambda _i, c=combo: preset_selected(c, c.property('previous') or 0)
    )
    COMBOS.append(combo)
    return combo
