# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Download sources: the built-in ones, the ones added by the user (STAC
API) and the check of their links. """

import json
import urllib.request

from qgis.PyQt.QtCore import QSettings

SETTING_KEY = 'RasterClassification/custom_sources'

# address tested for each built-in source (a small request, no account)
BUILTIN_CHECKS = {
    'Sentinel-2': 'https://catalogue.dataspace.copernicus.eu/odata/v1/'
                  'Products?$top=1',
    'Sentinel-2_AWS': 'https://earth-search.aws.element84.com/v1/'
                      'collections/sentinel-2-l2a',
    'Landsat_MPC': 'https://planetarycomputer.microsoft.com/api/stac/v1/'
                   'collections/landsat-c2-l2',
    'Sentinel-2_MPC': 'https://planetarycomputer.microsoft.com/api/stac/v1/'
                      'collections/sentinel-2-l2a',
    'Landsat_HLS': 'https://cmr.earthdata.nasa.gov/search/collections.json?'
                   'concept_id=C2021957657-LPCLOUD',
    'Sentinel-2_HLS': 'https://cmr.earthdata.nasa.gov/search/'
                      'collections.json?concept_id=C2021957295-LPCLOUD',
    'MODIS_09Q1_MPC': 'https://planetarycomputer.microsoft.com/api/stac/v1/'
                      'collections/modis-09Q1-061',
    'MODIS_11A2_MPC': 'https://planetarycomputer.microsoft.com/api/stac/v1/'
                      'collections/modis-11A2-061',
    'ASTER_MPC': 'https://planetarycomputer.microsoft.com/api/stac/v1/'
                 'collections/aster-l1t',
    'Copernicus_DEM_30_MPC': 'https://planetarycomputer.microsoft.com/api/'
                             'stac/v1/collections/cop-dem-glo-30',
}


def load():
    """ Sources added by the user: list of dictionaries. """
    try:
        data = json.loads(str(QSettings().value(SETTING_KEY, '[]')))
        return [d for d in data if isinstance(d, dict) and d.get('name')]
    except (ValueError, TypeError):
        return []


def save(sources):
    QSettings().setValue(SETTING_KEY, json.dumps(sources))


def parse_assets(text):
    return [a.strip() for a in str(text).split(',') if a.strip()]


def register(configurations, source):
    """ Make a source available to the search and the download. """
    configurations.custom_stac_sources[source['name']] = {
        'url': source['url'], 'collection': source['collection'],
        'assets': parse_assets(source.get('assets', ''))
    }
    configurations.product_description[source['name']] = (
        'STAC source added by the user %s (collection %s)'
        % (source['url'], source['collection'])
    )


def unregister(configurations, name):
    configurations.custom_stac_sources.pop(name, None)
    configurations.product_description.pop(name, None)


def check_address(source_name, custom=None):
    """ Address to test for a source. """
    if source_name in BUILTIN_CHECKS:
        return BUILTIN_CHECKS[source_name]
    if custom:
        return '%s/collections/%s' % (
            custom['url'].rstrip('/').replace('/search', ''),
            custom['collection'])
    return None


def check_links(addresses, timeout=10):
    """ Test the addresses: {name: address} -> {name: (ok, text)}. It runs
    in a background task: no QGIS object is used here. """
    results = {}
    for name, address in addresses.items():
        if not address:
            results[name] = (False, '-')
            continue
        try:
            request = urllib.request.Request(
                address, headers={'User-Agent': 'RasterClassification'}
            )
            with urllib.request.urlopen(request, timeout=timeout) as answer:
                results[name] = (200 <= answer.status < 400,
                                 'HTTP %s' % answer.status)
        except urllib.error.HTTPError as err:
            results[name] = (False, 'HTTP %s' % err.code)
        except Exception as err:
            results[name] = (False, str(err)[:60])
    return results
