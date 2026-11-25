# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Automatic detection of the satellite from the names of the band files.

The detection is only a convenience: the Wavelength menu can always be
changed manually, and a manual choice is never overwritten.
"""

import os
import re

# (regular expression on the file name, key found in the Wavelength menu)
# bands above 7 of Landsat 8/9 select the "raw" list with 11 bands
_S2 = re.compile(
    r'(^|[_\W])(S2[ABCD]_|MSIL[12][AC]_|T\d{2}[A-Z]{3}_\d{8}T\d{6}_)',
    re.IGNORECASE
)
_S2_BAND = re.compile(r'_B(0[1-9]|1[0-2]|8A)(_\d+m)?\.[A-Za-z0-9]+$|'
                      r'_B(0[1-9]|1[0-2]|8A)(_\d+m)?$', re.IGNORECASE)
_LANDSAT = re.compile(r'^L([COTEM])0?([1-9])_', re.IGNORECASE)
_LANDSAT_BAND = re.compile(r'_B(\d{1,2})(\.[A-Za-z0-9]+)?$', re.IGNORECASE)

RULES = [
    ('Sentinel-3', re.compile(r'^S3[AB]_', re.IGNORECASE)),
    ('ASTER', re.compile(r'^(AST_|ASTER)', re.IGNORECASE)),
    ('Pleiades', re.compile(r'(^|[_\W])PHR1[AB]', re.IGNORECASE)),
    ('WorldView-2 -3', re.compile(r'(^|[_\W])WV0?[23]', re.IGNORECASE)),
    ('RapidEye', re.compile(r'(^|[_\W])RapidEye', re.IGNORECASE)),
    ('SPOT 4', re.compile(r'(^|[_\W])SPOT_?4', re.IGNORECASE)),
    ('SPOT 5', re.compile(r'(^|[_\W])SPOT_?5', re.IGNORECASE)),
    ('SPOT 6', re.compile(r'(^|[_\W])SPOT_?6', re.IGNORECASE)),
]

# set when the user chooses the satellite manually (not overwritten)
manual = False
# set when the satellite was chosen by the detection
detected = False


def _detect_one(name):
    """ Key of the satellite for a file name, or None. """
    if _S2.search(name) and _S2_BAND.search(name):
        return 'Sentinel-2'
    m = _LANDSAT.match(name)
    if m:
        sensor, number = m.group(1).upper(), int(m.group(2))
        band = _LANDSAT_BAND.search(os.path.splitext(name)[0])
        band_number = int(band.group(1)) if band else 0
        if sensor in ('C', 'O') and number in (8, 9):
            if band_number > 7:
                return 'Landsat 8/9 raw'
            return 'Landsat %s OLI' % number
        if sensor == 'E' and number == 7:
            return 'Landsat 7 ETM+'
        if sensor == 'T' and number in (4, 5):
            return 'Landsat 4-5 TM'
        if sensor == 'M' and number in (1, 2, 3):
            return 'Landsat 1-3 MSS'
        return None
    for key, pattern in RULES:
        if pattern.search(name):
            return key
    return None


def detect_satellite(paths):
    """ Return the menu key of the satellite of the band files, or None when
    the files do not clearly belong to one satellite. """
    keys = set()
    for path in paths:
        key = _detect_one(os.path.basename(str(path)))
        if key is None:
            return None
        keys.add(key)
    if not keys:
        return None
    if keys == {'Landsat 8/9 raw', 'Landsat 8 OLI'}:
        return 'Landsat 8/9 raw'
    if keys == {'Landsat 8/9 raw', 'Landsat 9 OLI'}:
        return 'Landsat 8/9 raw'
    if len(keys) == 1:
        return keys.pop()
    return None


def find_menu_item(combo, key):
    """ Index of the Wavelength menu entry that contains the key. """
    for i in range(combo.count()):
        if combo.itemText(i).startswith(key):
            return i
    return -1


def reset():
    global manual, detected
    manual = False
    detected = False
