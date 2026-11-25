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
    QGridLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy,
    QGroupBox, QFrame
)
# noinspection PyUnresolvedReferences
from qgis.core import QgsApplication
from ..core import dock_progress
from .collapsible import CollapsibleBox
from ..core.language import tr, use_qm_files

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
        if QFileInfo(locale_path).exists() and use_qm_files():
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
        if QFileInfo(locale_path).exists() and use_qm_files():
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
        if QFileInfo(locale_path).exists() and use_qm_files():
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
        ui.frame_bandset.setFrameShape(QFrame.Shape.NoFrame)
        # group 1: the bands
        box_bands = CollapsibleBox('Band set', ui.frame_bandset, stretch=True)
        ui.box_bandset = box_bands
        inner = QVBoxLayout(box_bands.body)
        top = QHBoxLayout()
        top.addWidget(ui.toolButton_input_raster)
        top.addWidget(ui.add_loaded_bands_pushButton)
        top.addStretch(1)
        inner.addLayout(top)
        # the table of the bands (the plugin puts it in grid_bandset) and
        # the buttons that act on the selected bands
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
        inner.addLayout(middle, 1)
        # group 2: satellite and composition (the plugin adds the list and
        # the R, G, B lists)
        box_sat = CollapsibleBox('Satellite and composition',
                                 ui.frame_bandset)
        ui.box_satellite = box_sat
        composition = QGridLayout()
        row = QHBoxLayout()
        label = QLabel('Composition', ui.frame_bandset)
        ui.label_composition = label
        label.setToolTip('Color composition displayed for the band set')
        row.addWidget(label, 0)
        ui.horizontalLayout = row
        composition.addLayout(row, 0, 0, 1, 2)
        ui.gridLayout_2 = composition
        satellite = QHBoxLayout()
        ui.label_150.setText('Satellite')
        ui.label_150.setToolTip(
            'Satellite of the images: detected from the file names, '
            'and can be changed here')
        satellite.addWidget(ui.label_150, 0)
        satellite.addWidget(ui.wavelength_sat_combo, 1)
        inner_sat = QVBoxLayout(box_sat.body)
        inner_sat.addLayout(satellite)
        inner_sat.addLayout(composition)
        root.addWidget(box_bands, 1)
        root.addWidget(box_sat)
        old.addLayout(root, 1, 0, 1, 3)
        ui.bandset_root_layout = root

    def _rebuild_roi_layout(self):
        """ ROI tab in the order of the work: training file, class, drawing
        tools, then the list of the classes and ROIs (the largest part). """
        ui = self.ui
        ui.gridLayout_12.removeItem(ui.gridLayout_13)
        for layout, widgets in (
                (ui.gridLayout_4, (
                    ui.trainingFile_toolButton, ui.button_new_input,
                    ui.import_library_toolButton,
                    ui.export_signature_list_toolButton,
                    ui.delete_Signature_Button, ui.polygonROI_Button,
                    ui.pointerButton, ui.signature_spectral_plot_toolButton,
                    ui.delete_class_Button)),
                (ui.gridLayout_27, (
                    ui.undo_save_Button, ui.redo_save_Button, ui.label_44,
                    ui.ROI_Macroclass_ID_spin, ui.label_45,
                    ui.ROI_Macroclass_line, ui.button_Save_ROI)),
                (ui.gridLayout_10, (
                    ui.trainingFile_lineEdit, ui.button_reset_input))):
            for widget in widgets:
                layout.removeWidget(widget)
        ui.gridLayout_11.removeItem(ui.gridLayout_10)
        frame = ui.frame_2
        root = QVBoxLayout()
        root.setSpacing(6)
        # 1. training file
        ui.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        box_file = CollapsibleBox('Training file', frame)
        ui.box_file = box_file
        grid_file = QGridLayout(box_file.body)
        for column, widget in enumerate((
                ui.button_new_input, ui.trainingFile_toolButton,
                ui.import_library_toolButton,
                ui.export_signature_list_toolButton)):
            grid_file.addWidget(widget, 0, column)
            grid_file.setColumnStretch(column, 1)
        grid_file.addWidget(ui.trainingFile_lineEdit, 1, 0, 1, 3)
        grid_file.addWidget(ui.button_reset_input, 1, 3)
        root.addWidget(box_file)
        # 2. class: number, name, create, delete
        box_class = CollapsibleBox('Class', frame)
        ui.box_class = box_class
        row_class = QHBoxLayout(box_class.body)
        row_class.addWidget(ui.label_44)
        row_class.addWidget(ui.ROI_Macroclass_ID_spin)
        row_class.addWidget(ui.label_45)
        row_class.addWidget(ui.ROI_Macroclass_line, 1)
        row_class.addWidget(ui.button_Save_ROI)
        row_class.addWidget(ui.delete_class_Button)
        root.addWidget(box_class)
        # 3. ROI: drawing tools, undo and redo, delete, spectral plot
        box_roi = CollapsibleBox('ROI', frame)
        ui.box_roi = box_roi
        grid_roi = QGridLayout(box_roi.body)
        grid_roi.addWidget(ui.polygonROI_Button, 0, 0)
        grid_roi.addWidget(ui.pointerButton, 0, 1)
        grid_roi.addWidget(ui.undo_save_Button, 0, 2)
        grid_roi.addWidget(ui.redo_save_Button, 0, 3)
        grid_roi.addWidget(ui.delete_Signature_Button, 1, 0, 1, 2)
        grid_roi.addWidget(ui.signature_spectral_plot_toolButton, 1, 2, 1, 2)
        for column in range(4):
            grid_roi.setColumnStretch(column, 1)
        root.addWidget(box_roi)
        # 4. the list takes the free space
        ui.sig_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        box_list = CollapsibleBox('Classes and ROIs', frame, stretch=True)
        ui.box_list = box_list
        layout_list = QVBoxLayout(box_list.body)
        layout_list.addWidget(ui.sig_widget)
        root.addWidget(box_list, 1)
        ui.gridLayout_12.addLayout(root, 1, 0, 1, 1)
        ui.gridLayout_12.setRowStretch(1, 1)

    def retranslate_custom(self):
        """ Texts written by hand, in the language of the plugin (called at
        the creation and each time the language changes). """
        ui = self.ui
        try:
            tabs = ui.bandset_roi_tabs
            names = ('Band set definition', 'ROI && Classification',
                     'Download products', 'Settings')
            for index in range(min(tabs.count(), len(names))):
                tabs.setTabText(index, tr(names[index]))
            tabs.tabBar().setToolTip('')
            ui.label_composition.setText(tr('Composition'))
            ui.label_150.setText(tr('Satellite'))
            ui.box_file.setTitle(tr('Training file'))
            ui.box_class.setTitle(tr('Class'))
            ui.box_roi.setTitle(tr('ROI'))
            ui.box_processing.setTitle(tr('Processing'))
            ui.box_bandset.setTitle(tr('Band set'))
            ui.box_satellite.setTitle(tr('Satellite and composition'))
            ui.box_list.setTitle(tr('Classes and ROIs'))
            ui.pointerButton.setText(tr('Circle'))
            ui.button_Save_ROI.setText(tr('Create'))
            ui.delete_class_Button.setText(tr('Delete Class'))
            ui.delete_class_Button.setToolTip(
                tr('Delete the selected class with all its ROIs'))
            ui.previewButton.setToolTip(tr(
                'Preview: click to switch on, then click on the map; '
                'click again to switch off'))
            ui.pointerButton.setToolTip(tr(
                'Circle ROI: left click = center, move, right click = '
                'radius (adds the circle to the class)'))
            ui.polygonROI_Button.setToolTip(tr(
                'Polygon ROI: left click = vertex, right click = close '
                '(adds the polygon to the class)'))
            ui.button_Save_ROI.setToolTip(tr(
                'Create the class (number and name) that receives the '
                'ROIs'))
            boxes = getattr(ui, 'download_boxes', None)
            if boxes:
                for box, text in zip(boxes, ('Search parameters',
                                             'Product list', 'Download')):
                    box.setTitle(tr(text))
            page = getattr(ui, 'settings_page', None)
            if page is not None:
                page.retranslate()
        except Exception as err:
            str(err)

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
            box_processing = CollapsibleBox('Processing',
                                            classification_page)
            ui.box_processing = box_processing
            layout_processing = QVBoxLayout(box_processing.body)
            layout_processing.addWidget(ui.frame_3)
            ui.frame_3.setFrameShape(QFrame.Shape.NoFrame)
            ui.label_60.setVisible(False)
            page_layout.addWidget(box_processing, 0)
            tabs = QTabWidget(ui.dockWidgetContents)
            tabs.setObjectName('bandset_roi_tabs')
            tabs.addTab(ui.frame_bandset, 'Band set definition')
            tabs.addTab(classification_page, 'ROI && Classification')
            grid.addWidget(tabs, 2, 0, 1, 1)
            grid.setRowStretch(2, 1)
            ui.bandset_roi_tabs = tabs
            # the tabs share the width of the panel
            tabs.setUsesScrollButtons(False)
            tabs.tabBar().setExpanding(True)
            tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
            # the RGB= list is replaced by the predefined compositions; it
            # stays in the panel (hidden) because the plugin still uses it
            ui.label_61.setVisible(False)
            # simpler panel: no header (icon, version, manual), no title of
            # the ROI frame, no Image conversion and Download buttons (the
            # download is the third tab)
            for widget in (ui.scp_pushButton, ui.plugin_version_label2,
                           ui.userguide_toolButton_2, ui.label_48,
                           ui.image_conversion_toolButton_3,
                           ui.download_images_toolButton_2):
                widget.setVisible(False)
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
            self._rebuild_roi_layout()
            self.retranslate_custom()
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
        if QFileInfo(locale_path).exists() and use_qm_files():
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
        if QFileInfo(locale_path).exists() and use_qm_files():
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
