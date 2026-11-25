# SemiAutomaticClassificationPlugin
# The Semi-Automatic Classification Plugin for QGIS allows for the supervised
# classification of remote sensing images, providing tools for the download,
# the preprocessing and postprocessing of images.
# begin: 2012-12-29
# Copyright (C) 2012-2026 by Luca Congedo.
# Author: Luca Congedo
# Email: ing.congedoluca@gmail.com
#
# This file is part of SemiAutomaticClassificationPlugin.
# SemiAutomaticClassificationPlugin is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# SemiAutomaticClassificationPlugin is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with SemiAutomaticClassificationPlugin.
# If not, see <https://www.gnu.org/licenses/>.


import multiprocessing
import sys
from os import path, makedirs, remove
import ast

try:
    from .ui import resources_rc
    assert resources_rc
except Exception as error:
    print(error)

import qgis.utils as qgis_utils

global plugin_check

try:
    # import the PyQt libraries
    from qgis.PyQt.QtCore import (
        Qt, QFileInfo, QSettings, QSize, QTranslator, QCoreApplication,
        QDir, QDate
    )
    from qgis.PyQt.QtGui import QFont, QColor, QIcon
    from qgis.PyQt.QtWidgets import QApplication, QHeaderView, QLineEdit, QComboBox
    qt_check = True
    plugin_check = True
except Exception as error:
    print(error)
    qt_check = False
    plugin_check = False

# import the QGIS libraries
# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis, QgsWkbTypes, QgsApplication, QgsProject, QgsSettings
)
# noinspection PyUnresolvedReferences
from qgis.gui import QgsRubberBand

# import plugin version
from .__init__ import version as semiautomatic_class_version
# import SemiAutomaticClassificationPlugin
from .core import config as cfg
from .core import language, custom_sources, dock_progress
try:
    from .core import util_qgis
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )
try:
    from .core import util_qt
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )
try:
    from .core import utils
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )
try:
    from .core import util_gdal
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )
try:
    from .core import messages
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )
try:
    # initialize Qt ui
    from .ui.raster_classification_dialog import (
        RasterClassificationDialog, SpectralSignatureDialog,
        DockClassSimplifiedDialog,
        WidgetDialog
    )
except Exception as error:
    plugin_check = False
    qgis_utils.iface.messageBar().pushMessage(
        'Raster Classification', str(error), level=Qgis.Critical
    )


# minimum remotior sensus version
rs_version = '0.8.0'
lib_dir = rs_path = installed_version = remotior_sensus_2 = None


# Remotior Sensus is bundled with the plugin (offline use): prefer it
bundled_dir = path.dirname(path.abspath(__file__))
if path.isfile(path.join(bundled_dir, 'remotior_sensus', '__init__.py')):
    if bundled_dir in sys.path:
        sys.path.remove(bundled_dir)
    sys.path.insert(0, bundled_dir)

# find remotior sensus path if existing
for p in sys.path:
    candidate = path.join(p, 'remotior_sensus', '__init__.py')
    if path.isfile(candidate):
        rs_path = candidate
        break


def find_library_version(library_path):
    with open(library_path) as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, 'id', None) == '__version__':
                    # noinspection PyTypeChecker
                    return ast.literal_eval(node.value)
    return None


if rs_path is not None:
    installed_version = find_library_version(rs_path)


# download remotior sensus
def download_library(library_directory):
    try:
        import requests
        import tarfile
        import hashlib

        qgis_utils.iface.messageBar().pushMessage(
            'Raster Classification',
            QApplication.translate(
                'semiautomaticclassificationplugin',
                'Downloading Remotior Sensus package'
            ),
            level=Qgis.Info, duration=5
        )

        tar_name = f'remotior_sensus-{rs_version}.tar.gz'
        tar_url = (
            f'https://pypi.org/packages/source/r/remotior-sensus/{tar_name}'
        )
        tar_path = path.join(library_directory, tar_name)
        # download metadata
        metadata_response = requests.get(
            f'https://pypi.org/pypi/remotior-sensus/{rs_version}/json',
            timeout=30
        )
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        sha256_target = None
        for file in metadata.get('urls', []):
            if file.get('filename') == tar_name:
                sha256_target = file['digests']['sha256']
                break
        if not sha256_target:
            raise RuntimeError('SHA256 not found in PyPI metadata')
        # download tar
        response = requests.get(tar_url, timeout=60)
        response.raise_for_status()
        with open(tar_path, 'wb') as rs_file:
            rs_file.write(response.content)

        # check SHA256
        sha256 = hashlib.sha256()
        with open(tar_path, 'rb') as f:
            sha256.update(f.read())
        file_hash = sha256.hexdigest()
        if file_hash != sha256_target:
            remove(tar_path)
            raise RuntimeError('SHA256 check failed')

        # extract tar
        with (tarfile.open(tar_path, 'r:gz') as tar):
            base_dir = f'remotior_sensus-{rs_version}/src/remotior_sensus'
            for member in tar.getmembers():
                if not member.name.startswith(base_dir):
                    continue
                # check path
                target_path = str(path.join(library_directory, member.name))
                abs_base = path.abspath(library_directory)
                abs_target = path.abspath(target_path)
                if not abs_target.startswith(abs_base):
                    raise RuntimeError('Unsafe path detected in tar archive')
                rel_path = path.relpath(member.name, base_dir)
                file_path = path.join(
                    library_directory, 'remotior_sensus', rel_path
                )
                if member.isdir():
                    makedirs(file_path, exist_ok=True)
                else:
                    makedirs(path.dirname(file_path), exist_ok=True)
                    source_file = tar.extractfile(member)
                    if source_file:
                        with open(file_path, 'wb') as destination:
                            destination.write(source_file.read())

        try:
            remove(tar_path)
        except Exception as errr:
            str(errr)
        return True
    except Exception as errr:
        str(errr)
        # noinspection PyTypeChecker
        qgis_utils.iface.messageBar().pushMessage(
            'Raster Classification', str(errr),
            level=Qgis.Warning, duration=10
        )
        return False


try:
    # check Remotior Sensus version
    if installed_version is None or (
            float(f'{installed_version[0]}.{installed_version[2]}')
            < float(f'{rs_version[0]}.{rs_version[2]}')):
        plugin_check = False
        raise RuntimeError('rs version ')
    else:
        import remotior_sensus
        cfg.rs_version = remotior_sensus.__version__
        plugin_check = True
except Exception as error:
    str(error)
    try:
        lib_dir = bundled_dir
        sys.path.insert(0, lib_dir)

        if 'remotior_sensus' in sys.modules:
            del sys.modules['remotior_sensus']
        import remotior_sensus
        # check Remotior Sensus version
        if (float(f'{remotior_sensus.__version__[0]}.'
                  f'{remotior_sensus.__version__[2]}')
                < float(f'{rs_version[0]}.{rs_version[2]}')):
            raise RuntimeError('rs version ')
        cfg.rs_version = remotior_sensus.__version__
        plugin_check = True
    except Exception as error:
        str(error)
        # download library
        d_lib = download_library(lib_dir)
        if d_lib:
            try:
                sys.path.insert(0, lib_dir)
                if 'remotior_sensus' in sys.modules:
                    del sys.modules['remotior_sensus']
                import remotior_sensus
                cfg.rs_version = remotior_sensus.__version__
                plugin_check = False
                qgis_utils.iface.messageBar().pushMessage(
                    'Raster Classification',
                    QApplication.translate(
                        'semiautomaticclassificationplugin',
                        'Please, restart QGIS for executing the '
                        'Raster Classification'
                    ),
                    level=Qgis.Info, duration=20
                )
            except Exception as error:
                str(error)
                plugin_check = False
                qgis_utils.iface.messageBar().pushMessage(
                    'Raster Classification',
                    'Unable to load Remotior Sensus',
                    level=Qgis.Critical
                )
        else:
            plugin_check = False
            qgis_utils.iface.messageBar().pushMessage(
                'Raster Classification',
                'Unable to load Remotior Sensus',
                level=Qgis.Critical
            )


try:
    multiprocessing.freeze_support()
    # force spawn
    multiprocessing.set_start_method('spawn', force=True)
except Exception as error:
    str(error)


# noinspection PyPep8Naming
class RasterClassification:

    # noinspection PyArgumentList,PyTypeChecker
    def __init__(self, iface):
        if not qt_check:
            qgis_utils.iface.messageBar().pushMessage(
                'Raster Classification',
                'The installed version of Raster Classification '
                'requires Qt6. Please install a QGIS version with Qt6.',
                level=Qgis.Critical
            )
        if plugin_check:
            # import modules
            from .core.ui_utils import UiUtils
            from .interface import (
                input_interface, scp_dock, bandset_tab, settings,
                download_products_tab, image_conversion_tab,
                classification_tab, composition_presets
            )
            from .map_pointers.classification_preview_pointer import (
                ClassificationPreview)
            from .map_pointers.download_products_pointer import (
                DownloadProductsPointer)
            from .map_pointers.manual_roi_pointer import ManualROIPointer
            from .map_pointers.circle_roi_pointer import CircleROIPointer
            try:
                from .spectral_signature import (
                    spectral_signature_plot, signature_importer
                )
            except Exception as err:
                str(err)
                spectral_signature_plot = None
                signature_importer = None
            # system information
            cfg.system_platform = sys.platform
            # QGIS version
            qgis_ver = Qgis.QGIS_VERSION_INT
            # set multiprocess path
            python_path = None
            if cfg.system_platform.startswith('win'):
                try:
                    python_path = path.abspath(
                        path.join(sys.exec_prefix, 'pythonw.exe')
                    )
                    if path.isfile(python_path):
                        multiprocessing.set_executable(python_path)
                    else:
                        # from https://trac.osgeo.org/osgeo4w/ticket/392
                        python_path = path.abspath(
                            path.join(sys.exec_prefix, '../../bin/pythonw.exe')
                        )
                        if path.isfile(python_path):
                            multiprocessing.set_executable(python_path)
                        else:
                            qgis_utils.iface.messageBar().pushMessage(
                                'Raster Classification',
                                QApplication.translate(
                                    'semiautomaticclassificationplugin',
                                    'Error. Python library not found'
                                ),
                                level=Qgis.Info
                            )
                except Exception as err:
                    str(err)
            elif cfg.system_platform.startswith('darwin'):
                try:
                    python_path = path.abspath(
                        path.join(sys.exec_prefix, 'bin', 'python3')
                    )
                    if path.isfile(python_path):
                        multiprocessing.set_executable(python_path)
                    else:
                        python_path = path.abspath(
                            path.join(
                                sys.exec_prefix, '../Resources/bin/python3'
                            )
                        )
                        if path.isfile(python_path):
                            multiprocessing.set_executable(python_path)
                        else:
                            qgis_utils.iface.messageBar().pushMessage(
                                'Raster Classification',
                                QApplication.translate(
                                    'semiautomaticclassificationplugin',
                                    'Error. Python library not found'
                                ),
                                level=Qgis.Info
                            )
                except Exception as err:
                    str(err)
            # reference to QGIS interface
            cfg.iface = iface
            # reference to map canvas
            cfg.map_canvas = iface.mapCanvas()
            # language of the plugin: English (default) or French
            plugin_language = str(QSettings().value(
                language.SETTING_KEY, 'en'
            ))
            if plugin_language not in language.LANGUAGES:
                plugin_language = 'en'
            locale_settings = plugin_language
            language.set_language(plugin_language, remember=False)
            # plugin directory
            cfg.plugin_dir = ('%s/python/plugins/%s' % (
                QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path(),
                str(__name__).split('.')[0])
            )
            cfg.ui_utils = UiUtils()
            # create the dialog
            cfg.dialog = RasterClassificationDialog()
            cfg.dialog.destroyed.connect(dialog_deleted)
            try:
                # class dock dialog
                cfg.dock_class_simpl_dlg = DockClassSimplifiedDialog(
                    cfg.iface.mainWindow(), cfg.iface
                )
                cfg.input_interface = input_interface
                # welcome dialog
                cfg.widget_dialog = WidgetDialog()
            except Exception as err:
                str(err)
                qgis_utils.iface.messageBar().pushMessage(
                    'Raster Classification',
                    QApplication.translate(
                        'semiautomaticclassificationplugin',
                        'Please, restart QGIS for executing the '
                        'Raster Classification'
                    ),
                    level=Qgis.Info
                )
            try:
                cfg.utils = utils
                cfg.util_qgis = util_qgis
                cfg.util_qt = util_qt
                cfg.util_gdal = util_gdal
                # spectral signature plot dialog
                cfg.spectral_plot_dlg = SpectralSignatureDialog()
                cfg.settings = settings
                cfg.bst = bandset_tab
                cfg.signature_plot = spectral_signature_plot
                cfg.signature_importer = signature_importer
                cfg.usgs_spectral_lib = signature_importer.USGSSpectralLib()
                cfg.composition_presets = composition_presets
                cfg.image_conversion = image_conversion_tab
                interface_check = True
            except Exception as err:
                str(err)
                message = cfg.settings.test_all_dependencies()
                qgis_utils.iface.messageBar().pushMessage(
                    'Raster Classification', message,
                    level=Qgis.Critical
                )
                interface_check = False
            if interface_check:
                cfg.classification_preview_pointer = ClassificationPreview(
                    cfg.map_canvas
                )
                cfg.download_products = download_products_tab
                cfg.download_products_pointer = DownloadProductsPointer(
                    cfg.map_canvas
                )
                cfg.manual_roi_pointer = ManualROIPointer(cfg.map_canvas)
                cfg.circle_roi_pointer = CircleROIPointer(cfg.map_canvas)
                cfg.classification = classification_tab
                cfg.scp_dock = scp_dock
                # roi rubber band
                cfg.scp_dock_rubber_roi = QgsRubberBand(
                    cfg.map_canvas, QgsWkbTypes.LineGeometry
                )
                cfg.scp_dock_rubber_roi.setColor(QColor(0, 255, 255))
                cfg.scp_dock_rubber_roi.setWidth(2)
                # set font
                try:
                    q_set = QgsSettings()
                    f = q_set.value('qgis/stylesheet/fontFamily')
                    s = q_set.value('qgis/stylesheet/fontPointSize')
                    font = QFont()
                    font.setFamily(f)
                    font.setPointSize(int(s))
                    cfg.dialog.setFont(font)
                    cfg.dialog.ui.menu_treeWidget.setFont(font)
                except Exception as err:
                    str(err)
                registry_keys()
                # the panel is the only interface
                cfg.simplified = True
                # temporary directory
                cfg.temp_dir = get_temporary_directory()
                cfg.mx = messages
                log_level = (10 if cfg.qgis_registry[cfg.reg_log_key] == 2
                             else 20)
                try:
                    cfg.rs = remotior_sensus.Session(
                        n_processes=cfg.qgis_registry[cfg.reg_threads_value],
                        log_level=log_level, temporary_directory=cfg.temp_dir,
                        available_ram=cfg.qgis_registry[cfg.reg_ram_value],
                        multiprocess_module=multiprocessing,
                        progress_callback=cfg.ui_utils.update_bar,
                        messages_callback=cfg.mx, log_stream_handler=False
                    )
                except Exception as err:
                    str(err)
                    qgis_utils.iface.messageBar().pushMessage(
                        'Raster Classification',
                        QApplication.translate(
                            'semiautomaticclassificationplugin',
                            'Error starting Remotior Sensus'
                        ),
                        level=Qgis.Info
                    )
                if cfg.rs is not None:
                    # logger
                    cfg.logger = cfg.rs.configurations.logger
                    # create BandSet Catalog
                    cfg.bandset_catalog = cfg.rs.bandset_catalog()
                    cfg.dialog.ui.temp_directory_label.setText(cfg.temp_dir)
                    cfg.spectral_signature_plotter = (
                        cfg.signature_plot.SpectralSignaturePlot()
                    )
                    # info
                    sys_info = str(
                        'Raster Classification %s; QGIS v. %s; L: %s; OS: %s; python: %s; '
                        'remotior sensus: %s; environment: %s'
                        % (semiautomatic_class_version(), str(qgis_ver),
                           locale_settings, cfg.system_platform,
                           str(python_path),
                           str(remotior_sensus.__version__), str(lib_dir))
                    )
                    cfg.logger.log.info(sys_info)

    # init GUI
    # noinspection PyArgumentList,PyTypeChecker
    def initGui(self):
        if not qt_check:
            pass
        elif plugin_check is True and cfg.rs is not None:
            try:
                # the dock opens docked on the right side of the QGIS window
                dock_widget = cfg.dock_class_simpl_dlg
                cfg.iface.addDockWidget(
                    Qt.DockWidgetArea.RightDockWidgetArea, dock_widget
                )
                dock_widget.setFloating(False)
                # menu entry and toolbar button to show or hide the panel:
                # the panel can be opened again after it was closed
                show_action = dock_widget.toggleViewAction()
                show_action.setIcon(
                    QIcon('%s/raster_classification.png' % cfg.plugin_dir)
                )
                show_action.setText('Raster Classification')
                show_action.setToolTip(
                    'Show or hide the Raster Classification panel'
                )
                cfg.iface.addPluginToMenu('Raster Classification', show_action)
                cfg.iface.addToolBarIcon(show_action)
                cfg.show_action = show_action
            except Exception as err:
                str(err)
                qgis_utils.iface.messageBar().pushMessage(
                    'Raster Classification',
                    QApplication.translate(
                        'semiautomaticclassificationplugin',
                        'Please restart QGIS for installing the '
                        'Raster Classification'
                    ),
                    level=Qgis.Info
                )
            # bandset tab
            cfg.bst.add_satellite_to_combo(cfg.rs.configurations.sat_band_list)
            cfg.bst.add_unit_to_combo(cfg.rs.configurations.unit_list)
            cfg.classification.add_pretrained_model_info_to_combo(
                cfg.rs.configurations.pretrained_model_dict
            )
            cfg.classification.add_pretrained_segmentation_info_to_combo(
                cfg.rs.configurations.segmentation_model_dict
            )
            cfg.bst.add_band_set_tab_simplified()
            cfg.scp_dock.TrainingVectorLayer(signature_catalog=False,
                                             output_path=None)
            # set plugin version
            try:
                cfg.dialog.ui.plugin_version_label.setText(
                    semiautomatic_class_version()
                    + '\n(built on Remotior Sensus '
                    + str(remotior_sensus.__version__) + ')'
                )
            except Exception as err:
                str(err)
                cfg.dialog.ui.plugin_version_label.setText(
                    semiautomatic_class_version()
                )
            cfg.dock_class_simpl_dlg.ui.plugin_version_label2.setText(
                'Raster Classification %s' % semiautomatic_class_version()
            )
            algorithm_list = [
                cfg.rs.configurations.maximum_likelihood,
                cfg.rs.configurations.minimum_distance,
                cfg.rs.configurations.multi_layer_perceptron,
                cfg.rs.configurations.random_forest,
                cfg.rs.configurations.spectral_angle_mapping,
                cfg.rs.configurations.support_vector_machine,
            ]
            cfg.input_interface.add_algorithm_to_combo(algorithm_list)
            wavelength_sat_combo = (
                cfg.dock_class_simpl_dlg.ui.wavelength_sat_combo
            )
            wavelength_sat_combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow
            )
            wavelength_sat_combo.setMinimumContentsLength(10)
            cfg.dock_class_simpl_dlg.ui.alg_combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow
            )
            cfg.dock_class_simpl_dlg.ui.alg_combo.setMinimumContentsLength(
                10
            )
            # disabled band set boxes
            cfg.dialog.ui.band_set_comb_spinBox_2.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_9.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_12.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_5.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_16.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_17.setEnabled(False)
            cfg.dialog.ui.band_set_comb_spinBox_18.setEnabled(False)
            cfg.dialog.ui.macroclass_radioButton.setEnabled(False)
            cfg.dialog.ui.class_radioButton.setEnabled(False)
            # row height
            cfg.dialog.ui.download_images_tableWidget.verticalHeader(
            ).setDefaultSectionSize(24)
            cfg.dialog.ui.bands_tableWidget.verticalHeader(
            ).setDefaultSectionSize(24)
            # spectral signature threshold table
            cfg.util_qt.insert_table_column(
                cfg.dialog.ui.signature_threshold_tableWidget, 7,
                cfg.signature_id_column_name, 20, True
            )
            sig_table = cfg.dialog.ui.signature_threshold_tableWidget
            sig_table.verticalHeader(
            ).setDefaultSectionSize(24)
            cfg.dialog.ui.point_tableWidget.verticalHeader(
            ).setDefaultSectionSize(24)
            sig_list = cfg.spectral_plot_dlg.ui.signature_list_plot_tableWidget
            # spectral signature plot list
            cfg.util_qt.insert_table_column(
                sig_list, 6, cfg.signature_id_column_name, 20, True
            )
            cfg.util_qt.sort_table_column(sig_list, 3)
            cfg.util_qt.set_column_width_list(
                sig_list, [[0, 20], [1, 40], [2, 120], [3, 40], [4, 120],
                           [5, 20]]
            )
            sig_list.verticalHeader().setDefaultSectionSize(24)
            try:
                sig_list.horizontalHeader().setSectionResizeMode(
                    2, QHeaderView.ResizeMode.Stretch
                )
                sig_list.horizontalHeader().setSectionResizeMode(
                    4, QHeaderView.ResizeMode.Stretch
                )
            except Exception as err:
                str(err)
            # passwords
            cfg.dialog.ui.smtp_password_lineEdit.setEchoMode(
                QLineEdit.EchoMode.Password
            )
            cfg.dialog.ui.password_earthdata_lineEdit.setEchoMode(
                QLineEdit.EchoMode.Password
            )
            cfg.dialog.ui.password_copernicus_lineEdit.setEchoMode(
                QLineEdit.EchoMode.Password
            )
            # signature threshold
            cfg.util_qt.insert_table_column(
                sig_table, 7,
                cfg.signature_id_column_name, None, True
            )
            cfg.util_qt.set_column_width_list(
                sig_table, [[4, 100], [5, 100], [6, 100]]
            )
            try:
                sig_table.horizontalHeader().setSectionResizeMode(
                    1, QHeaderView.ResizeMode.Stretch
                )
                sig_table.horizontalHeader().setSectionResizeMode(
                    3, QHeaderView.ResizeMode.Stretch
                )
            except Exception as err:
                str(err)
            # product download tab
            cfg.util_qt.set_column_width_list(
                cfg.dialog.ui.download_images_tableWidget,
                [[0, 100], [1, 400]]
            )
            # set log state
            cfg.dialog.ui.log_checkBox.setCheckState(
                cfg.util_qt.check_state_from_value(
                    int(cfg.qgis_registry[cfg.reg_log_key])
                )
            )
            if cfg.rs is not None:
                if cfg.qgis_registry[cfg.reg_log_key] == 2:
                    # debug
                    cfg.rs.set(log_level=10)
                    cfg.mx.msg_inf_3()
                else:
                    # info
                    cfg.rs.set(log_level=20)
            cfg.logger.log.debug(
                'logger: %s' % cfg.qgis_registry[cfg.reg_log_key]
            )
            # set download news state
            cfg.dialog.ui.download_news_checkBox.setCheckState(
                cfg.util_qt.check_state_from_value(
                    int(cfg.qgis_registry[cfg.reg_download_news])
                )
            )
            # set raster compression
            cfg.dialog.ui.raster_compression_checkBox.setCheckState(
                cfg.util_qt.check_state_from_value(
                    int(cfg.qgis_registry[cfg.reg_raster_compression])
                )
            )
            # set ROI transparency
            cfg.dialog.ui.transparency_Slider.setValue(
                int(cfg.qgis_registry[cfg.reg_roi_transparency])
            )
            # gdal path
            cfg.dialog.ui.gdal_path_lineEdit.setText(
                cfg.qgis_registry[cfg.reg_gdal_path]
            )
            # ROI color
            cfg.dialog.ui.change_color_Button.setStyleSheet(
                'background-color :' + cfg.qgis_registry[cfg.reg_roi_color]
            )
            cfg.dialog.ui.transparency_Label.setText(
                QApplication.translate(
                    'semiautomaticclassificationplugin', 'Transparency '
                ) + str(cfg.qgis_registry[cfg.reg_roi_transparency]) + '%'
            )
            cfg.dialog.ui.transparency_Slider.setValue(
                cfg.qgis_registry[cfg.reg_roi_transparency]
            )
            # set SMTP checkbox state
            cfg.dialog.ui.smtp_checkBox.setCheckState(
                cfg.util_qt.check_state_from_value(
                    int(cfg.qgis_registry[cfg.reg_smtp_check])
                )
            )
            if cfg.qgis_registry[cfg.reg_smtp_check] == 2:
                cfg.smtp_notification = True
            else:
                cfg.smtp_notification = False
            # set sound state
            cfg.dialog.ui.sound_checkBox.setCheckState(
                cfg.util_qt.check_state_from_value(
                    int(cfg.qgis_registry[cfg.reg_sound])
                )
            )
            # raster variable name
            cfg.dialog.ui.variable_name_lineEdit.setText(
                cfg.qgis_registry[cfg.reg_raster_variable_name]
            )
            # group name
            cfg.dialog.ui.group_name_lineEdit.setText(
                cfg.qgis_registry[cfg.reg_group_name]
            )
            # hide tabs
            cfg.dialog.ui.SCP_tabs.setStyleSheet(
                'QTabBar::tab {padding: 0px; max-height: 0px;}'
            )
            # set window size
            cfg.dialog.blockSignals(True)
            cfg.dialog.resize(
                int(cfg.qgis_registry[cfg.reg_window_size_w]),
                int(cfg.qgis_registry[cfg.reg_window_size_h])
            )
            cfg.dialog.blockSignals(False)
            cfg.dialog.ui.widget.setMinimumSize(QSize(50, 0))
            cfg.dialog.ui.widget.setMaximumSize(QSize(400, 16777215))
            cfg.dialog.ui.splitter.setSizes(
                cfg.qgis_registry[cfg.reg_splitter_sizes]
            )
            # set RAM value
            cfg.dialog.ui.RAM_spinBox.setValue(
                int(cfg.qgis_registry[cfg.reg_ram_value])
            )
            # set CPU value
            cfg.dialog.ui.CPU_spinBox.setValue(
                cfg.qgis_registry[cfg.reg_threads_value]
            )
            try:
                # set SMTP server
                cfg.dialog.ui.smtp_server_lineEdit.setText(
                    cfg.qgis_registry[cfg.reg_smtp_server]
                )
                # set SMTP to emails
                cfg.dialog.ui.to_email_lineEdit.setText(
                    cfg.qgis_registry[cfg.reg_smtp_emails]
                )
                # set SMTP user and password
                cfg.dialog.ui.smtp_user_lineEdit.setText(
                    cfg.qgis_registry[cfg.reg_smtp_user]
                )
                # removed
                """
                if len(cfg.qgis_registry[cfg.reg_smtp_pass]) > 0:
                    smtp_pass = cfg.utils.decrypt_password(
                        cfg.qgis_registry[cfg.reg_smtp_pass].decode('UTF-8')
                    )
                    cfg.dialog.ui.smtp_password_lineEdit.setText(
                        smtp_pass.decode('UTF-8')
                    )
                    cfg.qgis_registry[
                        cfg.reg_smtp_pass] = cfg.utils.encrypt_password(
                        smtp_pass.decode('UTF-8')
                    )
                    cfg.smtp_pass = (smtp_pass.decode('UTF-8'))
                """
            except Exception as err:
                str(err)
            cfg.smtp_user = cfg.qgis_registry[
                cfg.reg_smtp_user]
            cfg.smtp_recipients = cfg.qgis_registry[
                cfg.reg_smtp_emails]
            cfg.smtp_server = cfg.qgis_registry[
                cfg.reg_smtp_server]
            try:
                # set earthdata user and password
                cfg.dialog.ui.user_earthdata_lineEdit.setText(
                    cfg.qgis_registry[cfg.reg_earthdata_user]
                )
                """
                if cfg.qgis_registry[cfg.reg_earthdata_pass] is not None:
                    earthdata_pass = cfg.utils.decrypt_password(
                        cfg.qgis_registry[
                            cfg.reg_earthdata_pass].decode('UTF-8')
                    )
                    cfg.dialog.ui.password_earthdata_lineEdit.setText(
                        earthdata_pass.decode('UTF-8')
                    )
                """
            except Exception as err:
                str(err)
            try:
                # set copernicus user and password
                cfg.dialog.ui.user_copernicus_lineEdit.setText(
                    cfg.qgis_registry[cfg.reg_copernicus_user]
                )
                """
                if cfg.qgis_registry[cfg.reg_copernicus_pass] is not None:
                    copernicus_pass = cfg.utils.decrypt_password(
                        cfg.qgis_registry[
                            cfg.reg_copernicus_pass].decode('UTF-8')
                    )
                    cfg.dialog.ui.password_copernicus_lineEdit.setText(
                        copernicus_pass.decode('UTF-8')
                    )
                """
            except Exception as err:
                str(err)
            cfg.dialog.ui.dateEdit_to.setDate(QDate.currentDate())
            cfg.dialog.ui.dateEdit_from.setDate(
                QDate.currentDate().addDays(-365)
            )
            # add satellite list to combo
            try:
                for product in (
                        cfg.rs.configurations.product_description.keys()):
                    cfg.dialog.ui.landsat_satellite_combo.addItem(product)
            except Exception as err:
                str(err)
                # backward compatibility remotior sensus < 0.2
                for product in cfg.rs.configurations.product_list:
                    cfg.dialog.ui.landsat_satellite_combo.addItem(product)
            # sources added by the user
            try:
                for source in custom_sources.load():
                    custom_sources.register(cfg.rs.configurations, source)
                    cfg.dialog.ui.landsat_satellite_combo.addItem(
                        source['name'])
            except Exception as err:
                str(err)
            # add color list to combo
            cfg.usgs_spectral_lib.add_spectral_library_to_combo()
            # bandset virtual raster
            cfg.virtual_bandset_name = QApplication.translate(
                'semiautomaticclassificationplugin', 'Virtual Band Set '
            )
            cfg.bandset_tab_name = QApplication.translate(
                'semiautomaticclassificationplugin', 'Band set '
            )
            cfg.scp_layer_name = QApplication.translate(
                'semiautomaticclassificationplugin', 'SCP training layer'
            )
            # connect to project loaded
            QgsProject.instance().readProject.connect(
                self.project_loaded
            )
            # connect to project saved
            QgsProject.instance().projectSaved.connect(
                self.project_saved
            )
            cfg.iface.newProjectCreated.connect(self.new_project_loaded)
            cfg.dialog.ui.help_textBrowser.setSearchPaths([cfg.temp_dir])
            cfg.logger.log.debug('init GUI')
            connect_gui()

    # save tables when saving project
    # noinspection PyArgumentList
    @staticmethod
    def project_saved():
        cfg.logger.log.debug('project_saved')
        cfg.project_registry[
            cfg.reg_bandset_count] = cfg.bandset_catalog.get_bandset_count()

        # download table
        cfg.download_products.save_download_table()
        for r in cfg.project_registry:
            cfg.util_qgis.write_project_variable(r, cfg.project_registry[r])
        # save bandset table
        for bandset_number in range(
                1, cfg.project_registry[cfg.reg_bandset_count] + 1
        ):
            xml = cfg.bandset_catalog.export_bandset_as_xml(
                bandset_number=bandset_number
            )
            xml = str(xml).replace('\n', '')
            cfg.util_qgis.write_project_variable(
                '%s%s' % (cfg.reg_bandset, bandset_number), xml
            )

    # new project
    @staticmethod
    def new_project_loaded():
        cfg.logger.log.debug('new_project_loaded')
        reset_scp()

    # read project variables
    @staticmethod
    def project_loaded():
        cfg.logger.log.debug('project_loaded')
        reset_scp()

    # remove plugin menu and icon
    # noinspection PyTypeChecker
    @staticmethod
    def unload():
        if qt_check:
            # write registry keys
            try:
                for r in cfg.qgis_registry:
                    cfg.util_qt.write_registry_keys(r, cfg.qgis_registry[r])
            except Exception as err:
                try:
                    cfg.logger.log.error(str(err))
                except Exception as err:
                    str(err)
            try:
                language.uninstall()
            except Exception as err:
                str(err)
            try:
                cfg.logger.log.debug('unload')
                cfg.rs.close()
            except Exception as err:
                str(err)
            try:
                rs_dir = ('%s/python/plugins/%s' % (
                            QFileInfo(
                                QgsApplication.qgisUserDatabaseFilePath()
                            ).path(), str(__name__).split('.')[0])
                          )
                sys.path.remove(rs_dir)
            except Exception as err:
                str(err)
            try:
                if cfg.show_action is not None:
                    qgis_utils.iface.removePluginMenu(
                        'Raster Classification', cfg.show_action)
                    qgis_utils.iface.removeToolBarIcon(cfg.show_action)
                    cfg.show_action = None
            except Exception as err:
                str(err)
            try:
                if cfg.dock_class_simpl_dlg is not None:
                    qgis_utils.iface.removeDockWidget(cfg.dock_class_simpl_dlg)
                cfg.dialog.deleteLater()
                """
                if cfg.dialog is not None:
                    qgis_utils.iface.removeDockWidget(cfg.dialog)
                """
            # remove temp files
            except Exception as err:
                str(err)
                if plugin_check:
                    qgis_utils.iface.messageBar().pushMessage(
                        'Raster Classification',
                        QApplication.translate(
                            'semiautomaticclassificationplugin',
                            'Please, restart QGIS for executing the '
                            'Raster Classification'
                        ),
                        level=Qgis.Info
                    )



# apply the language to the whole panel
def apply_language():
    """ Apply the language to the whole panel; each step is independent, so
    one failure does not stop the others. """
    def step(function, *args):
        try:
            function(*args)
        except Exception as err:
            cfg.logger.log.error('apply_language %s: %s'
                                 % (getattr(function, '__name__', ''), err))
    dock = cfg.dock_class_simpl_dlg
    step(dock.ui.retranslateUi, dock)
    step(cfg.dialog.ui.retranslateUi, cfg.dialog)
    step(dock.retranslate_custom)
    step(dock.apply_theme)
    step(cfg.composition_presets.retranslate)
    step(dock_progress.retranslate)
    step(cfg.bst.retranslate_table)
    if cfg.scp_training is not None and (
            cfg.scp_training.signature_catalog):
        step(cfg.scp_training.roi_signature_table_tree)


# get first installation
# noinspection PyArgumentList
def get_first_installation():
    cfg.first_install = cfg.util_qt.read_registry_keys(
        cfg.reg_first_install, 1
    )
    if cfg.first_install == 1:
        cfg.util_qt.write_registry_keys(cfg.reg_first_install, 0)
        cfg.util_qt.write_registry_keys(cfg.reg_simplified, 2)
        cfg.qgis_registry[cfg.reg_simplified] = 2
        cfg.utils.find_available_ram()
        cfg.utils.find_available_processors()
        qgis_utils.iface.messageBar().pushMessage(
            'Raster Classification',
            QApplication.translate(
                'semiautomaticclassificationplugin',
                'You are using the simplified interface. To change the '
                'interface go to Raster Classification > Settings and uncheck Simplified '
                'interface'
            ),
            level=Qgis.Info, duration=600
        )


# get temporary directory
# noinspection PyArgumentList
def get_temporary_directory():
    if cfg.temp_dir is None:
        temp_dir = str(QDir.tempPath() + '/' + cfg.temp_dir_name)
    else:
        temp_dir = cfg.temp_dir
    if not QDir(temp_dir).exists():
        try:
            makedirs(temp_dir)
        except Exception as err:
            str(err)
            cfg.util_qt.write_registry_keys(cfg.reg_temp_dir, temp_dir)
            cfg.temp_dir = str(QDir.tempPath() + '/' + cfg.temp_dir_name)
            temp_dir = cfg.temp_dir
            if not QDir(temp_dir).exists():
                makedirs(temp_dir)
    return temp_dir


# read registry keys
def registry_keys():
    cfg.temp_dir = cfg.util_qt.read_registry_keys(
        cfg.reg_temp_dir, cfg.temp_dir
    )
    for r in cfg.qgis_registry:
        cfg.qgis_registry[r] = cfg.util_qt.read_registry_keys(
            r, cfg.qgis_registry[r]
        )
    get_first_installation()


def connect_gui():
    cfg.classification_preview_pointer.leftClicked.connect(
        cfg.classification.pointer_left_click
    )
    cfg.classification_preview_pointer.rightClicked.connect(
        cfg.classification.pointer_right_click
    )
    cfg.download_products_pointer.leftClicked.connect(
        cfg.download_products.pointer_left_click
    )
    cfg.download_products_pointer.rightClicked.connect(
        cfg.download_products.pointer_right_click
    )
    cfg.circle_roi_pointer.leftClicked.connect(
        cfg.scp_dock.left_click_circle
    )
    cfg.circle_roi_pointer.rightClicked.connect(
        cfg.scp_dock.right_click_circle
    )
    cfg.circle_roi_pointer.moved.connect(cfg.scp_dock.moved_circle)
    cfg.manual_roi_pointer.leftClicked.connect(
        cfg.scp_dock.left_click_manual
    )
    cfg.manual_roi_pointer.rightClicked.connect(
        cfg.scp_dock.right_click_manual
    )
    """ Band set"""
    cfg.dialog.ui.toolButton_input_raster.clicked.connect(
        cfg.bst.add_file_to_band_set_action
    )
    # add loaded bands question box
    cfg.widget_dialog.ui.buttonBox.accepted.connect(cfg.bst.check_accepted)
    cfg.widget_dialog.ui.select_all_toolButton.clicked.connect(
        cfg.bst.select_all_bands
    )
    cfg.dialog.ui.add_loaded_bands_pushButton.clicked.connect(
        cfg.bst.add_loaded_band_to_bandset
    )
    cfg.dialog.ui.toolButton_custom_wavelength.clicked.connect(
        cfg.bst.set_custom_wavelength_action
    )
    cfg.dialog.ui.clear_bandset_toolButton.clicked.connect(
        cfg.bst.clear_bandset_action
    )
    cfg.dialog.ui.move_up_toolButton.clicked.connect(cfg.bst.move_up_band)
    cfg.dialog.ui.move_down_toolButton.clicked.connect(cfg.bst.move_down_band)
    cfg.dialog.ui.sort_by_name_toolButton.clicked.connect(
        cfg.bst.sort_bands_by_name
    )
    cfg.dialog.ui.remove_toolButton.clicked.connect(cfg.bst.remove_band)
    cfg.dialog.ui.add_band_set_toolButton.clicked.connect(
        cfg.bst.add_bandset_tab_action
    )
    cfg.dialog.ui.import_bandset_toolButton.clicked.connect(
        cfg.bst.import_bandset
    )
    cfg.dialog.ui.export_bandset_toolButton.clicked.connect(
        cfg.bst.export_bandset
    )
    cfg.dialog.ui.wavelength_sat_combo.currentIndexChanged.connect(
        cfg.bst.satellite_wavelength
    )
    cfg.dialog.ui.unit_combo.currentIndexChanged.connect(
        cfg.bst.satellite_unit
    )
    cfg.dialog.ui.bandset_dateEdit.dateChanged.connect(
        cfg.bst.set_bandset_date
    )
    cfg.dialog.ui.band_set_process_toolButton.clicked.connect(
        cfg.bst.perform_bandset_tools
    )
    cfg.dialog.ui.band_set_filter_lineEdit.textChanged.connect(
        cfg.bst.filter_table
    )
    cfg.dialog.ui.bandset_number_spinBox.valueChanged.connect(
        cfg.bst.change_bandset_tab_action
    )
    cfg.dialog.ui.bandset_tableWidget.doubleClicked.connect(
        cfg.bst.change_bandset_table_action
    )
    cfg.dialog.ui.bandset_date_lineEdit.editingFinished.connect(
        cfg.bst.edit_bandset_date
    )
    cfg.dialog.ui.root_dir_lineEdit.editingFinished.connect(
        cfg.bst.edit_bandset_root
    )
    cfg.dialog.ui.remove_bandset_toolButton.clicked.connect(
        cfg.bst.remove_bandsets
    )
    cfg.dialog.ui.move_down_toolButton_4.clicked.connect(
        cfg.bst.move_down_bandset
    )
    cfg.dialog.ui.move_up_toolButton_4.clicked.connect(cfg.bst.move_up_bandset)
    cfg.dialog.ui.sort_by_date.clicked.connect(cfg.bst.sort_bandsets_by_date)
    cfg.dialog.ui.rgb_toolButton.clicked.connect(cfg.bst.add_composite)

    """ SCP dock simplified """
    cfg.rgb_combo = cfg.dock_class_simpl_dlg.ui.rgb_combo
    cfg.rgb_combo.currentIndexChanged.connect(
        cfg.input_interface.rgb_combo_changed
    )
    # predefined compositions and spectral indices
    presets_combo = cfg.composition_presets.create_combo(
        cfg.dock_class_simpl_dlg.ui.frame_bandset, with_custom=True
    )
    cfg.dock_class_simpl_dlg.ui.horizontalLayout.addWidget(
        presets_combo, 1
    )
    # custom composition: one list of bands for each of R, G and B
    custom_widget = cfg.composition_presets.create_custom_widget(
        cfg.dock_class_simpl_dlg.ui.frame_bandset
    )
    cfg.dock_class_simpl_dlg.ui.gridLayout_2.addWidget(
        custom_widget, 1, 0, 1, 2
    )
    presets_combo.custom_widget = custom_widget
    # Download products (third tab) and Settings (fourth tab): the
    # widgets of the main window are placed in the panel (a placeholder
    # keeps the tab numbers of the window)
    try:
        from qgis.PyQt.QtWidgets import QWidget
        from .ui import download_layout
        from .ui.settings_page import SettingsPage
        dock_ui = cfg.dock_class_simpl_dlg.ui
        old_tabs = cfg.dialog.ui.SCP_tabs
        page = cfg.dialog.ui.tab_download_products
        index = old_tabs.indexOf(page)
        if index >= 0:
            old_tabs.removeTab(index)
            old_tabs.insertTab(index, QWidget(), 'Download products')
        scroll, boxes = download_layout.build(cfg.dialog.ui)
        dock_ui.bandset_roi_tabs.addTab(scroll, 'Download products')
        dock_ui.download_boxes = boxes
        dock_ui.download_wrapped = scroll.wrapped
        cfg.download_dock_page = scroll
        settings = SettingsPage(semiautomatic_class_version())
        settings.on_language_changed = apply_language
        settings.set_account_widgets(cfg.dialog.ui)
        dock_ui.bandset_roi_tabs.addTab(settings, 'Settings')
        dock_ui.settings_page = settings
        # locked while a processing runs; the navigation stays possible
        dock_progress.PANELS.append(dock_ui.bandset_roi_tabs)
        cfg.dock_class_simpl_dlg.retranslate_custom()
        cfg.dock_class_simpl_dlg.apply_theme()
    except Exception as err:
        cfg.logger.log.error('download tab: %s' % str(err))
    download_i = cfg.dock_class_simpl_dlg.ui.download_images_toolButton_2
    download_i.clicked.connect(
        cfg.input_interface.select_download_products_tab
    )
    wavelength_sat_combo = cfg.dock_class_simpl_dlg.ui.wavelength_sat_combo
    # locked, like the compositions, while a processing runs
    dock_progress.LOCKED.append(wavelength_sat_combo)
    wavelength_sat_combo.currentIndexChanged.connect(
        cfg.bst.set_satellite_wavelength_simplified
    )
    cfg.dock_class_simpl_dlg.ui.button_new_input.clicked.connect(
        cfg.scp_dock.create_training_input
    )
    cfg.dock_class_simpl_dlg.ui.button_reset_input.clicked.connect(
        cfg.scp_dock.reset_input
    )
    cfg.dock_class_simpl_dlg.ui.undo_save_Button.clicked.connect(
        cfg.scp_dock.undo_saved_roi
    )
    cfg.dock_class_simpl_dlg.ui.redo_save_Button.clicked.connect(
        cfg.scp_dock.redo_saved_roi
    )
    cfg.dock_class_simpl_dlg.ui.trainingFile_toolButton.clicked.connect(
        cfg.scp_dock.open_training_input_file
    )
    export_s = cfg.dock_class_simpl_dlg.ui.export_signature_list_toolButton
    export_s.clicked.connect(cfg.input_interface.export_signatures_tab)
    cfg.dock_class_simpl_dlg.ui.import_library_toolButton.clicked.connect(
        cfg.input_interface.import_signatures_tab
    )
    sign_s = cfg.dock_class_simpl_dlg.ui.signature_spectral_plot_toolButton
    sign_s.clicked.connect(cfg.scp_dock.add_signature_to_spectral_plot)
    cfg.dock_class_simpl_dlg.ui.delete_Signature_Button.clicked.connect(
        cfg.scp_dock.remove_selected_signatures
    )
    roi_spin = cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_ID_spin
    roi_spin.valueChanged.connect(cfg.scp_dock.roi_macroclass_id_value)
    roi_spin.valueChanged.connect(cfg.scp_dock.update_create_button)
    roi_line = cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_line
    roi_line.textChanged.connect(cfg.scp_dock.update_create_button)
    roi_line.editingFinished.connect(cfg.scp_dock.roi_macroclass_name_info)
    cfg.dock_class_simpl_dlg.ui.toolButton_input_raster.clicked.connect(
        cfg.bst.add_file_to_band_set_action
    )
    add_bands = cfg.dock_class_simpl_dlg.ui.add_loaded_bands_pushButton
    add_bands.clicked.connect(cfg.bst.add_loaded_band_to_bandset)
    cfg.dock_class_simpl_dlg.ui.clear_bandset_toolButton.clicked.connect(
        cfg.bst.clear_bandset_action
    )
    cfg.dock_class_simpl_dlg.ui.move_up_toolButton.clicked.connect(
        cfg.bst.move_up_band)
    cfg.dock_class_simpl_dlg.ui.move_down_toolButton.clicked.connect(
        cfg.bst.move_down_band)
    cfg.dock_class_simpl_dlg.ui.remove_toolButton.clicked.connect(
        cfg.bst.remove_band)
    cfg.dock_class_simpl_dlg.ui.polygonROI_Button.clicked.connect(
        cfg.scp_dock.pointer_manual_roi_active)
    cfg.dock_class_simpl_dlg.ui.pointerButton.clicked.connect(
        cfg.scp_dock.pointer_circle_roi_active)
    # Save creates the class; the ROIs are added to it by the right click
    cfg.dock_class_simpl_dlg.ui.button_Save_ROI.clicked.connect(
        cfg.scp_dock.create_class
    )
    cfg.dock_class_simpl_dlg.ui.previewButton.clicked.connect(
        cfg.classification.preview_button_clicked
    )
    # the button is released when another map tool is chosen
    cfg.map_canvas.mapToolSet.connect(
        cfg.classification.map_tool_changed
    )
    cfg.dock_class_simpl_dlg.ui.delete_class_Button.clicked.connect(
        cfg.scp_dock.delete_selected_classes
    )
    cfg.dock_class_simpl_dlg.ui.alg_combo.currentIndexChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dock_class_simpl_dlg.ui.button_classification.clicked.connect(
        cfg.classification.run_classification_action_simplified
    )

    """ Download product"""
    cfg.dialog.ui.find_images_toolButton.clicked.connect(
        cfg.download_products.find_images
    )
    cfg.dialog.ui.selectUL_toolButton_3.clicked.connect(
        cfg.download_products.pointer_active
    )
    cfg.dialog.ui.toolButton_display.clicked.connect(
        cfg.download_products.display_images
    )
    cfg.dialog.ui.toolButton_OSM.clicked.connect(
        cfg.download_products.display_osm
    )
    cfg.dialog.ui.remove_image_toolButton.clicked.connect(
        cfg.download_products.remove_image_from_table
    )
    cfg.dialog.ui.clear_table_toolButton.clicked.connect(
        cfg.download_products.clear_table
    )
    cfg.dialog.ui.download_images_Button.clicked.connect(
        cfg.download_products.download_images_action
    )
    cfg.dialog.ui.export_links_Button.clicked.connect(
        cfg.download_products.export_links
    )
    cfg.dialog.ui.import_table_pushButton.clicked.connect(
        cfg.download_products.import_table_text
    )
    cfg.dialog.ui.export_table_pushButton.clicked.connect(
        cfg.download_products.export_table_to_text
    )
    cfg.dialog.ui.show_area_radioButton_2.clicked.connect(
        cfg.download_products.show_hide_area
    )
    cfg.dialog.ui.check_toolButton_2.clicked.connect(
        cfg.download_products.check_all_bands
    )
    cfg.dialog.ui.remember_user_checkBox_3.stateChanged.connect(
        cfg.download_products.remember_user_earthdata_checkbox
    )
    cfg.dialog.ui.user_earthdata_lineEdit.editingFinished.connect(
        cfg.download_products.remember_user_earthdata
    )
    cfg.dialog.ui.password_earthdata_lineEdit.editingFinished.connect(
        cfg.download_products.remember_user_earthdata
    )
    cfg.dialog.ui.remember_user_checkBox_5.stateChanged.connect(
        cfg.download_products.remember_user_copernicus_checkbox
    )
    cfg.dialog.ui.user_copernicus_lineEdit.editingFinished.connect(
        cfg.download_products.remember_user_copernicus
    )
    cfg.dialog.ui.password_copernicus_lineEdit.editingFinished.connect(
        cfg.download_products.remember_user_copernicus
    )
    cfg.dialog.ui.download_images_tableWidget.itemSelectionChanged.connect(
        cfg.download_products.table_click
    )
    cfg.dialog.ui.products_filter_lineEdit.textChanged.connect(
        cfg.download_products.filter_table
    )

    """ Export spectral signature """
    cfg.dialog.ui.export_SCP_pushButton.clicked.connect(
        cfg.scp_dock.export_signature_file
    )
    cfg.dialog.ui.export_SHP_pushButton.clicked.connect(
        cfg.scp_dock.export_signature_vector
    )
    cfg.dialog.ui.export_CSV_library_toolButton.clicked.connect(
        cfg.scp_dock.export_signature_as_csv
    )

    """ Import spectral signature """
    cfg.dialog.ui.open_library_pushButton.clicked.connect(
        cfg.scp_dock.import_library_file
    )
    cfg.dialog.ui.open_shapefile_pushButton.clicked.connect(
        cfg.scp_dock.open_vector
    )
    cfg.dialog.ui.import_shapefile_pushButton.clicked.connect(
        cfg.scp_dock.import_vector
    )
    cfg.dialog.ui.usgs_library_comboBox.currentIndexChanged.connect(
        cfg.usgs_spectral_lib.library_changed
    )
    cfg.dialog.ui.add_usgs_library_pushButton.clicked.connect(
        cfg.usgs_spectral_lib.add_signature_to_catalog
    )
    """ Classification """
    cfg.dialog.ui.toolBox_classification.currentChanged.connect(
        cfg.classification.changed_tab
    )
    cfg.dialog.ui.band_set_comb_spinBox_12.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.pytorch_radioButton.toggled.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.hidden_layers_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.activation_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.batch_size_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.max_features_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.kernel_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.gamma_lineEdit.textChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.max_iterations_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.training_proportion_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.alpha_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.learning_rate_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.number_trees_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.min_split_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.param_c_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.steps_SpinBox.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.steps_SpinBox_2.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.steps_SpinBox_3.valueChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.cross_validation_checkBox.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.cross_validation_checkBox_2.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.cross_validation_checkBox_3.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.best_estimator_checkBox.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.best_estimator_checkBox_2.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.best_estimator_checkBox_3.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.class_weight_checkBox.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.class_weight_checkBox_2.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.ovr_checkBox.stateChanged.connect(
        cfg.classification.reset_preview
    )
    cfg.dialog.ui.macroclass_radioButton.toggled.connect(
        cfg.classification.macroclass_radio
    )
    cfg.dialog.ui.class_radioButton.toggled.connect(
        cfg.classification.class_radio
    )
    cfg.dialog.ui.linear_scaling_radioButton.toggled.connect(
        cfg.classification.linear_scaling_radio
    )
    cfg.dialog.ui.z_score_radioButton.toggled.connect(
        cfg.classification.z_scaling_radio
    )
    cfg.dialog.ui.pretrained_model_combo.currentIndexChanged.connect(
        cfg.classification.pretrained_model_info
    )
    cfg.dialog.ui.pretrained_model_combo_2.currentIndexChanged.connect(
        cfg.classification.pretrained_model_info_2
    )
    cfg.dialog.ui.pretrained_model_combo_3.currentIndexChanged.connect(
        cfg.classification.pretrained_model_info_3
    )
    cfg.dialog.ui.load_classifier_Button.clicked.connect(
        cfg.classification.open_classifier
    )
    cfg.dialog.ui.button_classification.clicked.connect(
        cfg.classification.run_classification_action
    )
    cfg.dialog.ui.save_classifier_button.clicked.connect(
        cfg.classification.save_classifier_action
    )
    cfg.dialog.ui.classification.clicked.connect(cfg.classification.set_script)
    """ Spectral signature plot """
    cfg.spectral_plot_dlg.ui.band_lines_checkBox.stateChanged.connect(
        cfg.spectral_signature_plotter.refresh_plot
    )
    cfg.spectral_plot_dlg.ui.grid_checkBox.stateChanged.connect(
        cfg.spectral_signature_plotter.grid_checkbox
    )
    cfg.spectral_plot_dlg.ui.sigma_checkBox.stateChanged.connect(
        cfg.spectral_signature_plotter.sigma_checkbox
    )
    cfg.spectral_plot_dlg.ui.add_signature_list_pushButton.clicked.connect(
        cfg.spectral_signature_plotter.add_to_signature_list
    )
    cfg.spectral_plot_dlg.ui.remove_Signature_Button.clicked.connect(
        cfg.spectral_signature_plotter.remove_signature
    )
    cfg.spectral_plot_dlg.ui.fitToAxes_pushButton.clicked.connect(
        cfg.spectral_signature_plotter.fit_plot_to_axes
    )
    button_1 = cfg.spectral_plot_dlg.ui.calculate_spectral_distance_Button
    button_1.clicked.connect(
        cfg.spectral_signature_plotter.calculate_spectral_distances
    )
    cfg.spectral_plot_dlg.ui.plot_text_spinBox.valueChanged.connect(
        cfg.spectral_signature_plotter.set_plot_legend_length
    )
    cfg.spectral_plot_dlg.ui.save_plot_pushButton.clicked.connect(
        cfg.spectral_signature_plotter.save_plot
    )
    table_1 = cfg.spectral_plot_dlg.ui.signature_list_plot_tableWidget
    table_1.doubleClicked.connect(
        cfg.spectral_signature_plotter.signature_list_double_click
    )
    table_1.cellChanged.connect(cfg.spectral_signature_plotter.edited_cell)

    cfg.logger.log.debug('GUI connected')


# get deleted dialog
def dialog_deleted():
    cfg.dialog = None


# reset all variables and interface
def reset_scp():
    cfg.logger.log.debug('reset_scp')
    if cfg.dialog is None:
        cfg.dialog = RasterClassificationDialog()
        cfg.dialog.destroyed.connect(dialog_deleted)
    cfg.ui_utils.set_interface(False)
    # clear band set
    t = cfg.dialog.ui.Band_set_tabWidget.count()
    for index in reversed(list(range(0, t))):
        cfg.bst.delete_bandset_tab(index)
    cfg.bandset_catalog = cfg.rs.bandset_catalog()
    # noinspection PyTypeChecker
    cfg.dock_class_simpl_dlg.ui.label_48.setText(
        QApplication.translate('semiautomaticclassificationplugin',
                               ' ROI & Signature list')
    )
    cfg.rgb_combo = cfg.dock_class_simpl_dlg.ui.rgb_combo
    cfg.utils.refresh_vector_layer()
    # reset tabs
    count = cfg.dialog.ui.Band_set_tabWidget.count()
    for i in list(reversed(range(0, count))):
        cfg.bst.delete_bandset_tab(i)
    cfg.bst.add_band_set_tab()
    cfg.bst.add_band_set_tab_simplified()
    cfg.dialog.ui.Band_set_tabWidget.blockSignals(True)
    cfg.project_path = QgsProject.instance().fileName()
    cfg.last_saved_dir = path.dirname(cfg.project_path)
    cfg.util_qt.clear_table(
        cfg.spectral_plot_dlg.ui.signature_list_plot_tableWidget
    )
    cfg.util_qt.clear_table(cfg.dialog.ui.signature_threshold_tableWidget)
    cfg.util_qt.clear_table(cfg.dialog.ui.download_images_tableWidget)
    cfg.scp_dock.TrainingVectorLayer(signature_catalog=False, output_path=None)
    # read variables
    cfg.bandset_tabs = {}
    cfg.project_registry = cfg.project_registry_default.copy()
    cfg.utils.read_project_variables()
    cfg.ui_utils.set_interface(True)
    # hide tabs
    cfg.dialog.ui.SCP_tabs.setStyleSheet(
        'QTabBar::tab {padding: 0px; max-height: 0px;}'
    )
