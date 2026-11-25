# Development notes

## Layout

| Folder | Content |
|---|---|
| `raster_classification.py` | plugin entry point (`classFactory` is in `__init__.py`) |
| `core/` | configuration, messages, Qt and QGIS helpers |
| `interface/` | one module per tool of the panel (band set, classification, ROI, download...), plus `composition_presets.py` (predefined compositions and indices) and `satellite_detection.py` |
| `ui/` | Qt Designer files (`.ui`) and the generated Python; the panel tabs are built in `raster_classification_dialog.py` |
| `spectral_signature/`, `map_pointers/` | signature plots and map tools |
| `remotior_sensus/` | bundled processing library (unmodified, version 0.8.0) |
| `core/language.py`, `core/fr_translations.py`, `core/fr_extra.py` | English and French of the interface |
| `dev/build_zip.py` | builds the installable zip |
| `releases/` | the zip to install in QGIS |

## Names

The code uses the Raster Classification names (`raster_classification.py`, class `RasterClassification`,
`raster_classification_dialog.py`, icons `raster_classification_*.svg`, Qt resource prefix
`:/plugins/raster_classification/`). A few internal identifiers of the original plugin are kept on purpose:

* the Qt translation context `semiautomaticclassificationplugin` (and the contexts of the generated `ui_*.py`
  files): the French dictionaries (`core/fr_translations.py`, `core/fr_extra.py`) are keyed by the source texts;
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

English is the default; French is chosen in the *Settings* tab (stored in the QGIS setting
`RasterClassification/language`, `en` or `fr`). The texts written by hand go through `core/language.py:tr()`, the
generated interfaces through the dictionary translator installed by `set_language()`.

## Code kept

Only the code used by the four tabs of the panel is kept: band set, ROI and classification, download, settings. The
other tools of the original plugin (band calculation, clustering, PCA, mosaic, Processing algorithms, ...) and the
unused functions of the bundled Remotior Sensus library were removed.

## Line endings

The sources use CRLF line endings. Keep them when editing, to keep the diffs small.

## Licence

GNU General Public License version 3 or later. Keep the copyright notices of Luca Congedo in the files derived from the
Semi-Automatic Classification Plugin.
