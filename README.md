# Raster Classification

**Supervised classification of remote sensing images in QGIS, with tools to download, preprocess and postprocess Landsat and Sentinel-2 images.**

*A plugin created and maintained by [ANABA MANGA](https://anbmng.com). Version 1.0.0.*

Raster Classification provides a set of intertwined tools for raster processing in order to build an automatic workflow
and ease land cover classification, also for people whose main field is not remote sensing. Search and download is
available for Landsat and Sentinel-2 images, and several algorithms are available for the classification.

## Installation

Raster Classification is available for QGIS 3.34 or later, including QGIS 4 (Qt 5 and Qt 6). It is built on the Remotior Sensus library, installed
automatically if missing, and requires GDAL (OGR), NumPy, SciPy and Matplotlib.

Download the latest zip from [`releases/`](releases) and install it in QGIS with
*Plugins > Manage and Install Plugins > Install from ZIP*. The interface is in English by default.

To build the zip yourself: `python dev/build_zip.py`.

## Credits and license

Raster Classification is derived from the
[Semi-Automatic Classification Plugin (SCP)](https://github.com/semiautomaticgit/SemiAutomaticClassificationPlugin)
by Luca Congedo (copyright 2012-2026), distributed under the GNU General Public License version 3 or later.
The changes (name, identity, interface, English default) are copyright 2026 ANABA MANGA and are released under the same
license, as the GPL requires; the original copyright notices are kept in the source files.

If you use the underlying classification workflow in a publication, please cite:
Congedo, Luca (2021). Semi-Automatic Classification Plugin: A Python tool for the download and processing of remote
sensing images in QGIS. Journal of Open Source Software, 6(64), 3172, https://doi.org/10.21105/joss.03172
