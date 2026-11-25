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


from qgis.PyQt.QtCore import (Qt, QFileInfo, QSettings, qVersion, QCoreApplication,
                          QTranslator)
from qgis.PyQt.QtWidgets import (
    QDialog, QDockWidget, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
# noinspection PyUnresolvedReferences
from qgis.core import QgsApplication
from ..core import dock_progress

from .ui_raster_classification import (
    Ui_RasterClassification
)
from .ui_raster_classification_dock_class import Ui_DockClass
from .ui_raster_classification_dock_class_simplified import (
    Ui_DockClassSimplified)
from .ui_raster_classification_scatter_plot import Ui_ScatterPlot
from .ui_raster_classification_signature_plot import (
    Ui_SpectralSignaturePlot
)
from .ui_raster_classification_widget import Ui_SCP_Widget

try:
    cfg = __import__(
        str(__name__).split('.')[0] + '.core.config', fromlist=['']
    )
except Exception as error:
    str(error)


# create the dialog
class RasterClassificationDialog(QDialog):
    # noinspection PyArgumentList
    def __init__(self):
        QDialog.__init__(self)
        try:
            self.setWindowFlags(Qt.WindowType.Window)
        except Exception as err:
            str(err)
            return
        # initialize plugin directory
        self.plugin_dir = QFileInfo(
            QgsApplication.qgisUserDatabaseFilePath()
        ).path() + '/python/plugins/RasterClassification'
        # locale name
        self.locale_name = QSettings().value('locale/userLocale')[0:2]
        # path to locale
        locale_path = ''
        if QFileInfo(self.plugin_dir).exists():
            locale_path = ('%s/i18n/raster_classification_%s.qm'
                           % (self.plugin_dir, self.locale_name))
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Set up the user interface from Designer.
        self.ui = Ui_RasterClassification()
        self.ui.setupUi(self)

    def shape_clip_combo(self, shape):
        self.ui.shapefile_comboBox.addItem(shape)

    def vector_to_raster_combo(self, vector):
        self.ui.vector_name_combo.addItem(vector)

    def classification_layer_combo(self, layer):
        self.ui.classification_name_combo.addItem(layer)

    def classification_layer_combo_2(self, layer):
        self.ui.classification_name_combo_2.addItem(layer)

    def classification_report_combo(self, layer):
        self.ui.classification_report_name_combo.addItem(layer)

    def classification_to_vector_combo(self, layer):
        self.ui.classification_vector_name_combo.addItem(layer)

    def reclassification_combo(self, layer):
        self.ui.reclassification_name_combo.addItem(layer)

    def reference_layer_combo(self, shape):
        self.ui.reference_name_combo.addItem(shape)

    def reference_layer_combo_2(self, shape):
        self.ui.reference_name_combo_2.addItem(shape)

    def raster_layer_combo(self, layer):
        self.ui.raster_name_combo.addItem(layer)

    def raster_extent_combo(self, layer):
        self.ui.raster_extent_combo.addItem(layer)

    def raster_extent_combo_2(self, layer):
        self.ui.raster_extent_combo_2.addItem(layer)

    def cloud_mask_raster_combo(self, layer):
        self.ui.classification_name_combo_4.addItem(layer)

    def reference_raster_combo(self, layer):
        self.ui.reference_raster_name_combo.addItem(layer)

    def project_raster_combo(self, layer):
        self.ui.raster_align_comboBox.addItem(layer)

    def class_field_combo(self, field):
        self.ui.class_field_comboBox.addItem(field)

    def class_field_combo_2(self, field):
        self.ui.class_field_comboBox_2.addItem(field)

    def class_field_combo_3(self, field):
        self.ui.class_field_comboBox_3.addItem(field)

    def reference_field_combo(self, field):
        self.ui.field_comboBox.addItem(field)

    def statistic_name_combo2(self, field):
        self.ui.statistic_name_combobox_2.addItem(field)

    def vector_edit_raster_combo(self, vector):
        self.ui.vector_name_combo_2.addItem(vector)

    def edit_raster_combo(self, layer):
        self.ui.edit_raster_name_combo.addItem(layer)

    def zonal_stat_raster_combo(self, layer):
        self.ui.classification_name_combo_5.addItem(layer)

    def vector_zonal_raster_combo(self, vector):
        self.ui.reference_name_combo_3.addItem(vector)

    def zonal_reference_field_combo(self, field):
        self.ui.class_field_comboBox_4.addItem(field)

    def reference_field_combo2(self, field):
        self.ui.field_comboBox_2.addItem(field)


# create the dialog
class DockClassDialog(QDockWidget):
    # noinspection PyArgumentList,PyUnusedLocal
    def __init__(self, parent, iface):
        QDockWidget.__init__(self)
        # initialize plugin directory
        try:
            self.plugin_dir = QFileInfo(
                QgsApplication.qgisUserDatabaseFilePath()
            ).path() + '/python/plugins/RasterClassification'
        except Exception as err:
            str(err)
            return
        # locale name
        self.locale_name = QSettings().value('locale/userLocale')[0:2]
        # path to locale
        locale_path = ''
        if QFileInfo(self.plugin_dir).exists():
            locale_path = ('%s/i18n/raster_classification_%s.qm'
                           % (self.plugin_dir, self.locale_name))
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.ui = Ui_DockClass()
        self.ui.setupUi(self)


# create the dialog
class DockClassSimplifiedDialog(QDockWidget):
    # noinspection PyArgumentList,PyUnusedLocal
    def __init__(self, parent, iface):
        QDockWidget.__init__(self)
        # initialize plugin directory
        try:
            self.plugin_dir = QFileInfo(
                QgsApplication.qgisUserDatabaseFilePath()
            ).path() + '/python/plugins/RasterClassification'
        except Exception as err:
            str(err)
            return
        # locale name
        self.locale_name = QSettings().value('locale/userLocale')[0:2]
        # path to locale
        locale_path = ''
        if QFileInfo(self.plugin_dir).exists():
            locale_path = ('%s/i18n/raster_classification_%s.qm'
                           % (self.plugin_dir, self.locale_name))
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.ui = Ui_DockClassSimplified()
        self.ui.setupUi(self)
        self._build_tabs()

    def _rebuild_bandset_layout(self):
        """ More ergonomic band set tab: the table takes the space, the
        buttons are grouped around it, then composition and satellite. """
        ui = self.ui
        old = ui.gridLayout_5
        # detach the old arrangement (the widgets are reused)
        old.removeItem(ui.gridLayout_8)
        old.removeItem(ui.horizontalLayout_4)
        for layout, widgets in (
                (ui.gridLayout_2, (
                    ui.toolButton_input_raster, ui.add_loaded_bands_pushButton,
                    ui.move_up_toolButton, ui.move_down_toolButton,
                    ui.remove_toolButton, ui.clear_bandset_toolButton)),
                (ui.horizontalLayout_4, (ui.label_150,
                                         ui.wavelength_sat_combo))):
            for widget in widgets:
                layout.removeWidget(widget)
        root = QVBoxLayout()
        root.setSpacing(6)
        # top: load the bands, reset
        top = QHBoxLayout()
        top.addWidget(ui.toolButton_input_raster)
        top.addWidget(ui.add_loaded_bands_pushButton)
        top.addStretch(1)
        root.addLayout(top)
        # middle: the table of the bands (the plugin puts it in grid_bandset)
        # and the buttons that act on the selected bands
        middle = QHBoxLayout()
        ui.grid_bandset = QGridLayout()
        middle.addLayout(ui.grid_bandset, 1)
        side = QVBoxLayout()
        side.addWidget(ui.move_up_toolButton)
        side.addWidget(ui.move_down_toolButton)
        side.addWidget(ui.remove_toolButton)
        side.addWidget(ui.clear_bandset_toolButton)
        side.addStretch(1)
        middle.addLayout(side, 0)
        root.addLayout(middle, 1)
        # composition (the plugin adds the list and the R, G, B lists)
        composition = QGridLayout()
        row = QHBoxLayout()
        label = QLabel('Composition', ui.frame_bandset)
        label.setToolTip('Color composition displayed for the band set')
        row.addWidget(label, 0)
        ui.horizontalLayout = row
        composition.addLayout(row, 0, 0, 1, 2)
        ui.gridLayout_2 = composition
        # satellite (wavelengths of the bands)
        satellite = QHBoxLayout()
        ui.label_150.setText('Satellite')
        ui.label_150.setToolTip(
            'Satellite of the images: detected from the file names, '
            'and can be changed here')
        satellite.addWidget(ui.label_150, 0)
        satellite.addWidget(ui.wavelength_sat_combo, 1)
        root.addLayout(satellite)
        root.addLayout(composition)
        old.addLayout(root, 1, 0, 1, 3)
        ui.bandset_root_layout = root

    def _build_tabs(self):
        """ Two tabs: the band set (color composition) and the
        classification workflow (ROI & signatures, then classification). """
        try:
            ui = self.ui
            self._rebuild_bandset_layout()
            grid = ui.gridLayout_14
            for frame in (ui.frame_bandset, ui.frame_2, ui.frame_3):
                grid.removeWidget(frame)
            # the first tab name replaces the dark title of the band set
            ui.label_59.setVisible(False)
            # ROI & signatures and classification belong to the same
            # processing: they share one tab, one above the other
            classification_page = QWidget(ui.dockWidgetContents)
            page_layout = QVBoxLayout(classification_page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.addWidget(ui.frame_2, 1)
            page_layout.addWidget(ui.frame_3, 0)
            tabs = QTabWidget(ui.dockWidgetContents)
            tabs.setObjectName('bandset_roi_tabs')
            tabs.addTab(ui.frame_bandset, 'Band set definition')
            tabs.addTab(classification_page, 'ROI && Classification')
            grid.addWidget(tabs, 2, 0, 1, 1)
            grid.setRowStretch(2, 1)
            ui.bandset_roi_tabs = tabs
            # the RGB= list is replaced by the predefined compositions; it
            # stays in the panel (hidden) because the plugin still uses it
            ui.label_61.setVisible(False)
            # the Pointer button draws circles
            ui.pointerButton.setText('Circle')
            # the button that creates the class is called Create
            ui.button_Save_ROI.setText('Create')
            # Delete Class takes the place of Spectral plot, which moves
            # under Polygon and Circle
            grid = ui.gridLayout_4
            grid.removeWidget(ui.signature_spectral_plot_toolButton)
            spacer = grid.itemAtPosition(4, 0)
            if spacer is not None and spacer.spacerItem() is not None:
                grid.removeItem(spacer)
            delete_class = QPushButton('Delete Class', ui.frame_2)
            delete_class.setStyleSheet(
                ui.delete_Signature_Button.styleSheet())
            delete_class.setIcon(ui.delete_Signature_Button.icon())
            delete_class.setIconSize(ui.delete_Signature_Button.iconSize())
            delete_class.setToolTip(
                'Delete the selected class with all its ROIs')
            grid.addWidget(delete_class, 2, 1, 1, 1)
            ui.delete_class_Button = delete_class
            grid.addWidget(ui.signature_spectral_plot_toolButton, 4, 0, 1, 1)
            grid.addItem(QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding), 5, 0, 1, 1)
            # the Preview button switches the preview on and off
            ui.previewButton.setCheckable(True)
            ui.previewButton.setToolTip(
                'Preview: click to switch on, then click on the map; '
                'click again to switch off')
            ui.pointerButton.setToolTip(
                'Circle ROI: left click = center, move, right click = '
                'radius (adds the circle to the class)')
            ui.polygonROI_Button.setToolTip(
                'Polygon ROI: left click = vertex, right click = close '
                '(adds the polygon to the class)')
            ui.button_Save_ROI.setToolTip(
                'Create the class (number and name) that receives the ROIs')
            ui.rgb_combo.setVisible(False)
            # progress bars under the Wavelength menu and the Algorithm row
            ui.bandset_progress = dock_progress.create_bar(ui.frame_bandset)
            ui.bandset_root_layout.addWidget(ui.bandset_progress)
            ui.classification_progress = dock_progress.create_bar(
                ui.frame_3
            )
            ui.gridLayout_6.addWidget(ui.classification_progress, 2, 0, 1, 4)
        except Exception as err:
            str(err)


# create the dialog
# noinspection PyMissingConstructor
class ScatterPlotDialog(QDialog):
    # noinspection PyArgumentList
    def __init__(self):
        QDockWidget.__init__(self)
        try:
            self.setWindowFlags(Qt.WindowType.Window)
        except Exception as err:
            str(err)
            return
        # initialize plugin directory
        self.plugin_dir = QFileInfo(
            QgsApplication.qgisUserDatabaseFilePath()
        ).path() + '/python/plugins/RasterClassification'
        # locale name
        self.locale_name = QSettings().value('locale/userLocale')[0:2]
        # path to locale
        locale_path = ''
        if QFileInfo(self.plugin_dir).exists():
            locale_path = ('%s/i18n/raster_classification_%s.qm'
                           % (self.plugin_dir, self.locale_name))
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.ui = Ui_ScatterPlot()
        self.ui.setupUi(self)


# noinspection PyMissingConstructor
class SpectralSignatureDialog(QDialog):
    # noinspection PyArgumentList
    def __init__(self):
        QDockWidget.__init__(self)
        self.setWindowFlags(Qt.WindowType.Window)
        # initialize plugin directory
        self.plugin_dir = QFileInfo(
            QgsApplication.qgisUserDatabaseFilePath()
        ).path() + '/python/plugins/RasterClassification'
        # locale name
        self.locale_name = QSettings().value('locale/userLocale')[0:2]
        # path to locale
        locale_path = ''
        if QFileInfo(self.plugin_dir).exists():
            locale_path = ('%s/i18n/raster_classification_%s.qm'
                           % (self.plugin_dir, self.locale_name))
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.ui = Ui_SpectralSignaturePlot()
        self.ui.setupUi(self)


# noinspection PyMissingConstructor
class WidgetDialog(QDialog):
    def __init__(self):
        QDockWidget.__init__(self)
        try:
            self.setWindowFlags(Qt.WindowType.Window)
        except Exception as err:
            str(err)
        self.ui = Ui_SCP_Widget()
        self.ui.setupUi(self)
