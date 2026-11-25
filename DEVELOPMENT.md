# Development notes

## Layout

| Folder | Content |
|---|---|
| `semiautomaticclassificationplugin.py` | plugin entry point (`classFactory` is in `__init__.py`) |
| `core/` | configuration, messages, Qt and QGIS helpers |
| `interface/` | one module per tool of the panel (band set, classification, ROI, download...), plus `composition_presets.py` (predefined compositions and indices) and `satellite_detection.py` |
| `ui/` | Qt Designer files (`.ui`) and the generated Python; the panel tabs are built in `semiautomaticclassificationplugindialog.py` |
| `qgis_processing/` | algorithms of the QGIS Processing toolbox |
| `spectral_signature/`, `map_pointers/` | signature plots and map tools |
| `remotior_sensus/` | bundled processing library (unmodified, version 0.8.0) |
| `i18n/` | translation files (the interface is in English by default) |
| `dev/build_zip.py` | builds the installable zip |
| `releases/` | the zip to install in QGIS |

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
