# Development notes

## Layout

| Folder | Content |
|---|---|
| `raster_classification.py` | plugin entry point (`classFactory` is in `__init__.py`) |
| `core/` | configuration, messages, Qt and QGIS helpers |
| `interface/` | one module per tool of the panel (band set, classification, ROI, download...), plus `composition_presets.py` (predefined compositions and indices) and `satellite_detection.py` |
| `ui/` | Qt Designer files (`.ui`) and the generated Python; the panel tabs are built in `raster_classification_dialog.py` |
| `qgis_processing/` | algorithms of the QGIS Processing toolbox |
| `spectral_signature/`, `map_pointers/` | signature plots and map tools |
| `remotior_sensus/` | bundled processing library (unmodified, version 0.8.0) |
| `i18n/` | translation files (the interface is in English by default) |
| `dev/build_zip.py` | builds the installable zip |
| `releases/` | the zip to install in QGIS |

## Names

The code uses the Raster Classification names (`raster_classification.py`, class `RasterClassification`,
`raster_classification_dialog.py`, icons `raster_classification_*.svg`, Qt resource prefix
`:/plugins/raster_classification/`). A few internal identifiers of the original plugin are kept on purpose:

* the Qt translation context `semiautomaticclassificationplugin` (and the contexts of the generated `ui_*.py`
  files): the translation files in `i18n/` are keyed by it, and the Qt tool that compiles them is not part of this
  repository's workflow;
* the file formats of the original plugin (`.scp`, `.scpx` training inputs and signature libraries), so that existing
  files still open;
* the `scp_*` attribute names of the configuration (`cfg.scp_dock`, `cfg.scp_training`...) and the matching
  project variables.

Renaming them is possible but would break old translations, files or projects.

## Qt 5 and Qt 6

The code imports Qt only through `qgis.PyQt`, so the same files run on QGIS 3.34+ (Qt 5) and QGIS 4 (Qt 6). Do not
import `PyQt5` or `PyQt6` directly.

## Build the zip

From the repository root:

```bash
python dev/build_zip.py
```

The script compiles every Python file (to catch syntax errors) and writes `releases/RasterClassification-1.0.0.zip`
with the files tracked by git. In QGIS: Plugins > Manage and Install Plugins > Install from ZIP, then restart QGIS.

## Language

English is the default. To follow the language of QGIS, set the QGIS setting `RasterClassification/language` to `auto`
(or to a locale code such as `fr`).

## Line endings

The sources use CRLF line endings. Keep them when editing, to keep the diffs small.

## Licence

GNU General Public License version 3 or later. Keep the copyright notices of Luca Congedo in the files derived from the
Semi-Automatic Classification Plugin.
