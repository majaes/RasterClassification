Raster Classification
=====================

**Supervised classification of remote sensing images in QGIS: colour compositions, spectral indices and land cover classification, in one panel.**

![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin-589632?logo=qgis&logoColor=white) ![version](https://img.shields.io/badge/version-1.0.0-0f6fb5) ![QGIS](https://img.shields.io/badge/QGIS-3.34%2B%20%7C%204.x-589632) ![Qt](https://img.shields.io/badge/Qt-5%20%7C%206-41cd52?logo=qt&logoColor=white) ![license](https://img.shields.io/badge/license-GPLv3%2B-e07b39) ![interface](https://img.shields.io/badge/interface-EN%20%7C%20FR-555)

*A plugin created, designed and maintained by [ANABA MANGA](https://anbmng.com).*

Raster Classification is designed first of all to make **land cover maps from satellite images** without being an
expert in remote sensing. You load the bands of an image (Sentinel-2, Landsat, ASTER...), choose a colour composition,
create the classes, draw a few training areas for each class and run the classification. The panel guides you from the
bands to the map, in four tabs:

1. **Color composition**: the band set, the satellite, the compositions and the spectral indices.
2. **SV Classification** (supervised classification): training file, classes, ROI, spectral signatures, preview and
   classification.
3. **Download products**: search and download of the images from several sources.
4. **Settings**: language, sources and accounts of the download, credits.

## Features

* **Band set**: load the bands of an image with *Open file* or *Add layer*, reorder them, and see the colour composition
  of the band set straight away (**natural colour by default**).
* **Automatic satellite detection** from the band file names (Sentinel-2, Landsat 1 to 9, ASTER, Sentinel-3...). The
  *Wavelength* menu can always be changed by hand, and a manual choice is never overwritten.
* **Predefined colour compositions**: natural colour, colour infrared, agriculture, healthy vegetation, short-wave
  infrared, urban, geology. The bands are found by themselves, and the entries whose bands are missing are greyed out
  with the missing bands in the tooltip.
* **Spectral indices** saved as a new layer with a colour ramp: NDVI, NDWI, NDBI and NBR.
* **ROI and spectral signatures**: draw training areas (polygon or circle), name the classes, plot the spectral
  signatures.
* **Classification** with several algorithms (maximum likelihood by default), with a *Preview* on a small area before
  running the whole image, plus tools for the pre- and post-processing of the images.
* **Works offline**: the processing library is bundled with the plugin.
* One panel docked on the right of QGIS, with four tabs: *Color composition*, *SV Classification*,
  *Download products* and *Settings*.
* **Download** from Copernicus Data Space (Sentinel-2), Earth Search on AWS (Sentinel-2 L2A, no account), Microsoft
  Planetary Computer (Landsat, Sentinel-2, MODIS, ASTER, Copernicus DEM) and NASA HLS. Other STAC catalogues can be added
  in *Settings*, where the links of all the sources can be checked.
* **English and French**: the language is changed in *Settings* without restarting QGIS.

## Requirements

QGIS **3.34 or later**, including **QGIS 3.44 (LTR)** and any **QGIS 4.x** (Qt 5 and Qt 6). The plugin bundles
Remotior Sensus and needs GDAL (OGR), NumPy, SciPy and Matplotlib, which come with QGIS. Some classifiers (for
example the Random Forest of scikit-learn) need the Python package `scikit-learn`, which is not included in QGIS:
the plugin warns when it is missing. The *Download products* tab needs an Internet connection (Copernicus or Earthdata
accounts); everything else works offline.

### Development and test environment

| Component | QGIS 3.44 LTR | QGIS 4.0 |
|---|---|---|
| QGIS | 3.44.15 | 4.0.1 |
| Qt | 5.15 | 6.8 |
| Python | 3.12 | 3.12 |
| GDAL / PROJ / GEOS | 3.13 / 9.8 / 3.15 | 3.12 / 9.7 / 3.14 |
| OS | Windows 11 | Windows 11 |

On QGIS 4.0.1 the plugin was used in the interface (loading Sentinel-2 bands, colour compositions, NDVI on a full
tile). On QGIS 3.44.15 the modules load and the panels are built; a complete run of the plugin in the interface is
still to be confirmed. Other systems (macOS, Linux) have not been tested.

## Installation

* **From QGIS**: Plugins > Manage and Install Plugins, search for *Raster Classification* (once published in the
  official plugin repository).
* **From a ZIP**: download `RasterClassification-1.0.0.zip` from the [releases](releases) folder, then Plugins >
  Manage and Install Plugins > Install from ZIP. Restart QGIS after the first installation.

## Usage

1. Open the panel from the *Raster Classification* menu.
2. In **Color composition**, click *Open file* and choose the bands of your image (for example `B02`, `B03`, `B04`,
   `B08` of a Sentinel-2 tile). The satellite is detected and the natural colour composition is displayed.
3. Choose another composition or an index in the list of predefined compositions.
4. In **SV Classification**, create a training file. Enter a class number and a name, then click *Save* to create
   the class. Draw its ROI: with *Polygon*, left click adds a vertex and right click closes the polygon; with
   *Circle*, left click sets the centre, move the cursor and right click sets the radius. The right click adds the
   ROI to the class at once. Check the signatures with *Spectral plot*.
5. Click *Preview* to test the classification on a small area, then *RUN* to classify the whole image.

## Data and licences

* Sentinel-2 and Landsat images: use the licence of your data provider (Copernicus, USGS).
* The *Download products* tab uses the services of Copernicus and NASA Earthdata with your own accounts; no password
  is stored by the plugin.
* [Remotior Sensus](https://github.com/semiautomaticgit/remotior_sensus) (bundled, unmodified, version 0.8.0) by Luca
  Congedo: GPL v3 or later.

## What is new in Raster Classification

Created and maintained by [ANABA MANGA](https://anbmng.com) (copyright (C) 2026):

* the single panel with four tabs (*Color composition*, *SV Classification*, *Download products*, *Settings*), with
  the same look in each tab and foldable sections;
* the predefined and custom colour compositions, the NDVI, NDWI, NDBI and NBR indices calculated in the background,
  and the automatic detection of the satellite;
* the workflow of the classes: create the class, draw its ROI as polygons or circles, a right click adds each ROI to
  the class, colours of the ROI by class, delete a class with its ROI;
* the switchable classification preview, the locking of all the options while a processing runs, the progress bars
  with *Cancel*;
* the download tab reorganised, the new source Earth Search (AWS, no account), the sources of your own (STAC), the
  check of the links, the repaired Landsat HLS and MODIS searches;
* the English and French interface, changed without restarting QGIS;
* the new design: icons, flat buttons, a code base reduced to what the panel uses.

## Data and licences

* Sentinel-2 and Landsat images: use the licence of your data provider (Copernicus, USGS).
* The *Download products* tab uses the services of Copernicus and NASA Earthdata with your own accounts; no password
  is stored by the plugin.
* [Remotior Sensus](https://github.com/semiautomaticgit/remotior_sensus) (bundled, unmodified, version 0.8.0) by Luca
  Congedo: GPL v3 or later.

## Credits and licence

**Raster Classification is a work by [ANABA MANGA](https://anbmng.com)**: name, interface, colour compositions,
indices, satellite detection and maintenance. Copyright (C) 2026 ANABA MANGA.

It is derived from the [Semi-Automatic Classification Plugin (SCP)](https://github.com/semiautomaticgit/SemiAutomaticClassificationPlugin)
by **Luca Congedo** (copyright 2012-2026), released under the GPL; the copyright notices of that project are kept in the
source files, as the licence requires. If you use the classification workflow in a publication, please cite:
Congedo, Luca (2021). Semi-Automatic Classification Plugin: A Python tool for the download and processing of remote
sensing images in QGIS. Journal of Open Source Software, 6(64), 3172, https://doi.org/10.21105/joss.03172

Raster Classification is free software released under the GNU General Public License, version 3 or (at your option)
any later version, see [LICENSE](LICENSE).

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md).
