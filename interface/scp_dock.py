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


from copy import deepcopy
from datetime import datetime, timedelta
import shutil
import zipfile

import numpy
from qgis.PyQt.QtCore import Qt, QPoint, QPointF, QMetaType
from qgis.PyQt.QtGui import (QColor, QFont, QCursor, QIcon, QPixmap, QPainter,
                         QPolygonF, QAction)
from qgis.PyQt.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QCompleter, QMenu,
    QApplication, QHeaderView
)
# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsGeometry, QgsFeature, QgsField, QgsPointXY, Qgis
)
# noinspection PyUnresolvedReferences
from qgis.gui import QgsVertexMarker, QgsHighlight

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])
from ..core.language import tr

try:
    from remotior_sensus.core.spectral_signatures import (
        SpectralSignaturesCatalog, SpectralSignaturePlot, generate_signature_id
    )
    from remotior_sensus.util import raster_vector
except Exception as error:
    SpectralSignaturesCatalog = str
    str(error)


""" Class to manage signature catalog buffer """


class SignatureCatalogBuffer:

    def __init__(self, signature_catalog, max_size):
        cfg.logger.log.debug(
            'SignatureCatalogBuffer max_size: %s' % str(max_size)
        )
        self.max_size = max_size
        self.buffer = {}
        for key in range(-max_size, max_size + 1):
            self.buffer[key] = None
        self.buffer[0] = signature_catalog

    def set_catalog(self, signature_catalog):
        # delete files of undo max size that will be replaced
        if -self.max_size in self.buffer:
            if self.buffer[-self.max_size] is not None:
                try:
                    cfg.utils.remove_file(
                        self.buffer[-self.max_size].geometry_file
                    )
                    cfg.utils.remove_file(
                        self.buffer[-self.max_size].temporary_file
                    )
                except Exception as err:
                    str(err)
                self.buffer[-self.max_size] = None
        # remove redo keys
        for i in range(1, self.max_size + 1):
            if i in self.buffer:
                if self.buffer[i] is not None:
                    # delete temporary signature file
                    try:
                        cfg.utils.remove_file(
                            self.buffer[i].geometry_file
                        )
                        cfg.utils.remove_file(
                            self.buffer[i].temporary_file
                        )
                    except Exception as err:
                        str(err)
                # remove redo keys
                self.buffer[i] = None
                cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(
                    False
                )
        # replace undo keys
        for key in sorted(self.buffer):
            if key < 0:
                self.buffer[key] = self.buffer[key + 1]
        self.buffer[0] = signature_catalog

    def undo(self):
        for key in reversed(range(-self.max_size, self.max_size)):
            self.buffer[key + 1] = self.buffer[key]
            if self.buffer[key + 1] is not None:
                cfg.logger.log.debug(
                    'self.buffer[%s].geometry_file: %s'
                    % ((key + 1), str(self.buffer[key + 1].geometry_file))
                )
        cfg.logger.log.debug('self.buffer: %s' % self.buffer)
        cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(True)
        cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(False)
        if self.buffer[-1] is not None:
            cfg.logger.log.debug('self.buffer[-1]: %s' % self.buffer[-1])
            cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
        return self.buffer[0]

    def redo(self):
        for key in range(-self.max_size + 1, self.max_size + 1):
            self.buffer[key - 1] = self.buffer[key]
            if self.buffer[key - 1] is not None:
                cfg.logger.log.debug(
                    'self.buffer[%s].geometry_file: %s'
                    % ((key - 1), str(self.buffer[key - 1].geometry_file))
                )
        cfg.logger.log.debug('self.buffer: %s' % self.buffer)
        cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
        cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
        if self.buffer[1] is not None:
            cfg.logger.log.debug('self.buffer[1]: %s' % self.buffer[1])
            cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(True)
        return self.buffer[0]



""" Class to manage signature catalog and vector input in QGIS """


# noinspection PyUnresolvedReferences
class TrainingVectorLayer:

    # noinspection PyArgumentList
    def __init__(
            self, signature_catalog: SpectralSignaturesCatalog,
            output_path: str
    ):
        # vector layer
        self.vector = None
        self.layer = None
        # layer editing
        self.editing = False
        # dictionary of items of ROI and signatures in dock tree
        self.class_dock_tree = {}
        # dictionary of items of macroclasses in dock tree
        self.macroclass_dock_tree = {}
        self.collapse_tree = True
        # reset classification preview classifier
        cfg.classifier_preview = None
        cfg.dock_class_simpl_dlg.ui.button_Save_ROI.setEnabled(True)
        cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(False)
        cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
        # reset
        # noinspection PySimplifyBooleanCheck
        if signature_catalog is False:
            # reset table tree
            self.tree = self.clear_tree()
            project = cfg.util_qgis.get_qgis_project()
            # remove training input
            if cfg.scp_training is not None:
                try:
                    project.removeMapLayer(cfg.scp_training.layer)
                except Exception as err:
                    str(err)
            cfg.scp_training = None
            cfg.project_registry[cfg.reg_training_input_path] = ''
            cfg.dock_class_simpl_dlg.ui.trainingFile_lineEdit.setText('')
        # init
        else:
            cfg.logger.log.debug(
                'TrainingVectorLayer output_path: %s' % str(output_path)
            )
            # create buffer
            self.signature_catalog_buffer = SignatureCatalogBuffer(
                signature_catalog,
                max_size=cfg.qgis_registry[cfg.reg_max_train_buffer]
            )
            self.signature_catalog = signature_catalog
            cfg.logger.log.debug(
                'signature_catalog %s' % str(signature_catalog)
            )
            self.temporary_file = (
                cfg.rs.configurations.temp.temporary_file_path(
                    name_suffix='.scpx'
                )
            )
            cfg.logger.log.debug(
                'self.temporary_file: %s' % str(self.temporary_file)
            )
            # define output path
            self.output_path = output_path
            cfg.logger.log.debug(
                'self.output_path: %s' % str(self.output_path)
            )
            cfg.project_registry[cfg.reg_training_input_path] = output_path
            cfg.dock_class_simpl_dlg.ui.trainingFile_lineEdit.setText(
                output_path)
            # create self.layer in map
            self.add_vector_to_map()
            # connect project saved
            cfg.util_qgis.get_qgis_project().projectSaved.connect(
                self.project_saved
            )
            # connect to table tree
            self.tree = self.roi_signature_table_tree()

    # disable editing
    # noinspection PyPep8Naming
    def beforeEditingStarted(self):
        if not self.editing:
            self.layer.commitChanges(stopEditing=True)
            cfg.mx.msg_inf_1()


    # save signature catalog to file
    def signature_catalog_copy(self):
        cfg.logger.log.debug('signature_catalog_copy')
        signature_catalog = deepcopy(self.signature_catalog)
        # copy geometry file to a temporary file on disk: the classification
        # runs in other processes (spawn), which cannot read /vsimem
        geometry_temp_path = (
            cfg.rs.configurations.temp.temporary_file_path(
                name_suffix='.gpkg'
            )
        )
        raster_vector.gdal_copy_vector(
            signature_catalog.geometry_file, geometry_temp_path)
        signature_catalog.geometry_file = geometry_temp_path
        return signature_catalog

    # update_bandset
    # noinspection PyUnresolvedReferences
    def update_bandset(self):
        cfg.logger.log.debug('update bandset')
        try:
            bandset_x = cfg.bandset_catalog.get(
                cfg.project_registry[cfg.reg_training_bandset_number]
            )
            if cfg.util_gdal.compare_crs(self.signature_catalog.crs,
                                         bandset_x.crs) is False:
                cfg.mx.msg_err_8()
                # noinspection PyTypeChecker
                cfg.logger.log.debug(
                    'signature_catalog.crs: %s; bandset_x.crs: %s'
                    % (str(self.signature_catalog.crs), bandset_x.crs)
                )
            else:
                self.signature_catalog.bandset = bandset_x
                cfg.mx.msg_inf_7()
        except Exception as err:
            str(err)

    # save signature catalog to file
    def project_saved(self):
        self.save_signature_catalog(path=self.output_path)
        # save backup
        self.save_signature_catalog(
            path='%s%s' % (self.output_path, cfg.backup_name)
        )

    # reset signature catalog
    # noinspection PyTypeChecker
    def reset_signature_catalog(self):
        cfg.logger.log.debug('reset_signature_catalog')
        project = cfg.util_qgis.get_qgis_project()
        try:
            project.removeMapLayer(self.layer)
        except Exception as err:
            str(err)
        cfg.map_canvas.setRenderFlag(False)
        cfg.map_canvas.setRenderFlag(True)
        self.signature_catalog_buffer = None
        self.signature_catalog = None
        self.vector = None
        self.layer = None
        self.output_path = ''
        cfg.dock_class_simpl_dlg.ui.trainingFile_lineEdit.setText('')
        cfg.project_registry[cfg.reg_training_input_path] = ''
        # reset table tree
        self.tree = self.clear_tree()
        self.macroclass_dock_tree = {}

    # save signature catalog to file
    def save_signature_catalog(self, path=None, signature_id_list=None):
        if path is None:
            path = self.output_path
        if self.signature_catalog is not None:
            self.signature_catalog.save(
                output_path=path, signature_id_list=signature_id_list
            )
            cfg.logger.log.debug('save_signature_catalog: %s' % str(path))
        else:
            cfg.logger.log.debug('save_signature_catalog: catalog is None')

    # save signature catalog to temporary file
    def save_temporary_signature_catalog(self):
        cfg.logger.log.debug('save_temporary_signature_catalog')
        if self.signature_catalog is not None:
            self.signature_catalog.save(self.temporary_file)
            cfg.logger.log.debug(
                'save_temporary_signature_catalog: %s'
                % str(self.temporary_file)
            )
        else:
            cfg.logger.log.debug('save_signature_catalog: catalog is None')

    # set new signature catalog
    # noinspection PyArgumentList
    def set_signature_catalog(self, signature_catalog):
        cfg.logger.log.debug('set_signature_catalog')
        self.signature_catalog_buffer.set_catalog(signature_catalog)
        self.signature_catalog = signature_catalog
        # create self.layer in map
        self.add_vector_to_map()

    # edit vector
    def edit_vector(self, expression, field_name, value):
        self.editing = True
        cfg.util_qgis.edit_layer_features(
            layer=self.layer, expression=expression, field_name=field_name,
            value=value
        )
        self.editing = False

    # undo signature catalog
    def undo(self):
        cfg.logger.log.debug('undo')
        if self.signature_catalog is not None:
            cfg.logger.log.debug(
                'self.signature_catalog.geometry_file: %s'
                % str(self.signature_catalog.geometry_file)
            )
        self.signature_catalog = self.signature_catalog_buffer.undo()
        # connect to table tree
        self.tree = self.roi_signature_table_tree()
        # create self.layer in map
        self.add_vector_to_map()

    # redo signature catalog
    def redo(self):
        cfg.logger.log.debug('redo')
        if self.signature_catalog is not None:
            cfg.logger.log.debug(
                'self.signature_catalog.geometry_file: %s'
                % str(self.signature_catalog.geometry_file)
            )
        self.signature_catalog = self.signature_catalog_buffer.redo()
        # connect to table tree
        self.tree = self.roi_signature_table_tree()
        # create self.layer in map
        self.add_vector_to_map()

    # add vector to map
    def add_vector_to_map(self):
        project = cfg.util_qgis.get_qgis_project()
        cfg.map_canvas.setRenderFlag(False)
        if self.layer is not None:
            try:
                project.removeMapLayer(self.layer)
                self.vector = None
            except Exception as err:
                str(err)
        if self.signature_catalog is not None:
            cfg.logger.log.debug(
                'self.signature_catalog.geometry_file: %s'
                % str(self.signature_catalog.geometry_file)
            )
        self.vector = cfg.util_qgis.add_vector_layer(
            self.signature_catalog.geometry_file, cfg.scp_layer_name, 'ogr'
        )
        self.vector.setReadOnly(True)
        self.vector.setCustomProperty('semiautomaticclassificationplugin', 'roi')
        self.layer = project.addMapLayer(self.vector)
        table_config = self.layer.attributeTableConfig()
        try:
            table_config.setColumnHidden(0, True)
            table_config.setColumnHidden(1, True)
            self.layer.setAttributeTableConfig(table_config)
            cfg.util_qgis.training_symbol(
                self.layer, self.signature_catalog.macroclasses_color_string,
                self.signature_catalog.macroclass_field
            )
        except Exception as err:
            cfg.logger.log.error(str(err))
        cfg.map_canvas.setRenderFlag(True)
        # disable layer editing
        self.layer.editingStarted.connect(self.beforeEditingStarted)


    # create ROI and signature table tree
    def roi_signature_table_tree(self, tree=None):
        cfg.logger.log.debug('roi_signature_table_tree')
        # reset classification preview classifier
        cfg.classifier_preview = None
        self.tree = self.clear_tree(tree)
        self.tree.blockSignals(True)
        self.tree.setSortingEnabled(False)
        macroclass_list = []
        # macroclasses
        for macroclass in self.signature_catalog.macroclasses:
            macroclass_name = self.signature_catalog.macroclasses[macroclass]
            macroclass_list.append(macroclass_name)
            if macroclass in self.signature_catalog.macroclasses_color_string:
                macroclass_color = (
                    self.signature_catalog.macroclasses_color_string[
                        macroclass
                    ]
                )
            else:
                macroclass_color = cfg.rs.shared_tools.random_color()
                self.signature_catalog.macroclasses_color_string[
                    macroclass] = macroclass_color
            # add macroclass items
            self.add_macroclass_tree_item(
                macroclass=macroclass, macroclass_info=macroclass_name,
                color=macroclass_color, checkbox_state=None
            )
        cfg.logger.log.debug('macroclass_list: %s' % str(macroclass_list))
        # add spectral signatures and ROIs
        if self.signature_catalog.table is None:
            signatures = []
        else:
            signatures = self.signature_catalog.table.signature_id.tolist()
        class_name_list = []
        for signature in signatures:
            if signature != 'N/A':
                signature_array = self.signature_catalog.table[
                    self.signature_catalog.table['signature_id'] == signature]
                macroclass_id = signature_array.macroclass_id[0]
                class_id = signature_array.class_id[0]
                class_name = signature_array.class_name[0]
                class_name_list.append(class_name)
                selected = signature_array.selected[0]
                geometry_check = signature_array.geometry[0]
                signature_check = signature_array.signature[0]
                color = signature_array.color[0]
                if signature_check == 1 and geometry_check == 1:
                    type_info = cfg.roi_and_signature_type
                elif geometry_check == 1:
                    type_info = cfg.roi_type
                elif signature_check == 1:
                    type_info = cfg.signature_type
                else:
                    type_info = ''
                    cfg.logger.log.error('type_info empty')
                # replace for checkbox state
                if selected == 1:
                    selected = 2
                self.add_class_tree_item(
                    macroclass_id=macroclass_id, class_id=class_id,
                    class_info=class_name, type_info=type_info,
                    signature_id=signature, color=color,
                    checkbox_state=selected
                )
        cfg.logger.log.debug('class_name_list: %s' % str(class_name_list))
        self.tree.show()
        self.tree.setSortingEnabled(True)
        self.tree.blockSignals(False)
        # info completer
        macroclass_info_completer(macroclass_list)
        # the ROIs take the color of their class on the map
        try:
            if self.layer is not None:
                cfg.util_qgis.training_symbol(
                    self.layer,
                    self.signature_catalog.macroclasses_color_string,
                    self.signature_catalog.macroclass_field
                )
        except Exception as err:
            cfg.logger.log.error(str(err))
        cfg.scp_training = self
        update_create_button()
        return self.tree

    # add signature item
    def add_class_tree_item(
            self, macroclass_id, class_id, class_info,
            type_info, signature_id, color=None, checkbox_state=None
    ):
        self.class_dock_tree[str(signature_id)] = QTreeWidgetItem()
        try:
            self.macroclass_dock_tree[macroclass_id].addChild(
                self.class_dock_tree[str(signature_id)]
            )
        except Exception as err:
            cfg.logger.log.error(str(err))
            self.add_macroclass_tree_item(macroclass=macroclass_id,
                                          macroclass_info='')
        self.class_dock_tree[str(signature_id)].setFlags(
            Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsUserCheckable |
            Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled
        )
        if checkbox_state is not None:
            self.class_dock_tree[str(signature_id)].setCheckState(
                0, cfg.util_qt.check_state_from_value(int(checkbox_state))
            )
        self.class_dock_tree[str(signature_id)].setData(
            0, 0, int(macroclass_id)
        )
        self.class_dock_tree[str(signature_id)].setData(1, 0, int(class_id))
        self.class_dock_tree[str(signature_id)].setData(2, 0, str(class_info))
        self.class_dock_tree[str(signature_id)].setData(3, 0, str(type_info))
        self.class_dock_tree[str(signature_id)].setData(
            5, 0, str(signature_id)
        )
        if color is not None and not cfg.simplified:
            self.class_dock_tree[str(signature_id)].setBackground(
                4, QColor(color)
            )

    # add macroclass item
    def add_macroclass_tree_item(
            self, macroclass, macroclass_info, color=None, checkbox_state=None
    ):
        row = self.tree.topLevelItemCount()
        self.macroclass_dock_tree[macroclass] = QTreeWidgetItem(row)
        self.tree.addTopLevelItem(self.macroclass_dock_tree[macroclass])
        self.macroclass_dock_tree[macroclass].setFlags(
            Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDropEnabled
        )
        self.macroclass_dock_tree[macroclass].setExpanded(True)
        self.macroclass_dock_tree[macroclass].setData(
            0, 0, int(macroclass)
        )
        self.macroclass_dock_tree[macroclass].setData(
            2, 0, str(macroclass_info)
        )
        self.macroclass_dock_tree[macroclass].setData(
            5, 0, int(macroclass)
        )
        font = QFont()
        font.setBold(True)
        self.macroclass_dock_tree[macroclass].setFont(0, font)
        self.macroclass_dock_tree[macroclass].setFont(2, font)
        if checkbox_state is not None:
            self.macroclass_dock_tree[macroclass].setCheckState(
                0, cfg.util_qt.check_state_from_value(checkbox_state)
            )
        if color is not None:
            self.macroclass_dock_tree[macroclass].setBackground(
                4, QColor(color)
            )

    # clear tree
    # noinspection PyUnresolvedReferences,PyTypeChecker
    def clear_tree(self, tree=None):
        cfg.logger.log.debug('clear_tree')
        self.class_dock_tree = {}
        self.macroclass_dock_tree = {}
        if tree is None:
            order = 0
            sorter = Qt.SortOrder.AscendingOrder
        else:
            order = tree.header().sortIndicatorOrder()
            sorter = tree.header().sortIndicatorSection()
            tree.deleteLater()
        cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget = (
            QTreeWidget(cfg.dock_class_simpl_dlg.ui.sig_widget)
        )
        tree_widget = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        tree_widget.setEditTriggers(
            QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        tree_widget.setAlternatingRowColors(True)
        tree_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        tree_widget.setIndentation(5)
        tree_widget.setExpandsOnDoubleClick(False)
        tree_widget.setObjectName('signature_list_treeWidget')
        tree_widget.setSortingEnabled(True)
        cfg.dock_class_simpl_dlg.ui.sig_gridLayout.addWidget(tree_widget,
                                                             1, 1, 1, 1)
        tree_widget.headerItem().setText(
            0, QApplication.translate('semiautomaticclassificationplugin',
                                      'Class')
        )
        tree_widget.headerItem().setText(
            1, QApplication.translate('semiautomaticclassificationplugin',
                                      'C ID')
        )
        tree_widget.headerItem().setText(
            2, QApplication.translate('semiautomaticclassificationplugin',
                                      'Name')
        )
        tree_widget.headerItem().setText(
            3, QApplication.translate('semiautomaticclassificationplugin',
                                      'Type')
        )
        tree_widget.headerItem().setText(
            4, QApplication.translate('semiautomaticclassificationplugin',
                                      'Color')
        )
        tree_widget.headerItem().setText(5, 'signature_id')
        # tree list
        tree_widget.header().hideSection(5)
        tree_widget.header().hideSection(1)
        tree_widget.header().hideSection(3)
        tree_widget.header().setSortIndicator(order, sorter)
        cfg.util_qt.set_tree_column_width_list(
            tree_widget, [[0, 60], [1, 30], [2, 260], [3, 40], [4, 30]]
        )
        # every column can be resized by hand; the last one (color) takes
        # the remaining width
        tree_widget.header().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )
        tree_widget.header().setStretchLastSection(True)
        # connect to edited cell
        tree_widget.itemChanged.connect(self.edited_cell_tree)
        tree_widget.itemSelectionChanged.connect(select_class_from_tree)
        # connect to signature list double click
        tree_widget.itemDoubleClicked.connect(self.signature_tree_double_click)
        #  context menu
        tree_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        tree_widget.customContextMenuRequested.connect(context_menu)
        return tree_widget

    # edit macroclass value
    def edit_macroclass(self, macroclass_value):
        ids = self.get_highlighted_ids()
        for signature_id in ids:
            # set macroclass in table
            old_value = self.signature_catalog.table.macroclass_id[
                self.signature_catalog.table['signature_id'] == signature_id
                ]
            self.signature_catalog.table.macroclass_id[
                self.signature_catalog.table[
                    'signature_id'] == signature_id] = macroclass_value
            # add macroclass in dictionary
            if macroclass_value not in self.signature_catalog.macroclasses:
                self.signature_catalog.macroclasses[macroclass_value] = (
                    'macroclass'
                )
                macroclass_color = (
                    cfg.rs.shared_tools.random_color()
                )
                self.signature_catalog.macroclasses_color_string[
                    macroclass_value] = macroclass_color
            # check if isolated macroclass
            check_id = self.signature_catalog.table.macroclass_id[
                self.signature_catalog.table[
                    'macroclass_id'] == old_value]
            if len(check_id) == 0:
                try:
                    del self.signature_catalog.macroclasses[
                        old_value]
                    del self.macroclass_dock_tree[old_value]
                    cat = self.signature_catalog
                    del cat.macroclasses_color_string[old_value]
                except Exception as err:
                    str(err)
            # set macroclass in geometry
            expression = '"%s" = \'%s\'' % (
                cfg.rs.configurations.uid_field_name, signature_id
            )
            self.edit_vector(
                expression=expression, field_name='macroclass_id',
                value=macroclass_value
            )

    # edited cell
    def edited_cell_tree(self, item, column):
        table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        table.setSortingEnabled(False)
        table.blockSignals(True)
        reload = False
        # items
        try:
            signature_id = list(self.class_dock_tree.keys())[
                list(self.class_dock_tree.values()).index(item)]
            macroclass_id = False
        except Exception as err:
            str(err)
            try:
                macroclass_id = list(self.macroclass_dock_tree.keys())[
                    list(self.macroclass_dock_tree.values()).index(item)]
                signature_id = False
            except Exception as err:
                cfg.logger.log.error(str(err))
                self.roi_signature_table_tree()
                return
        # item value
        value = item.text(column)
        cfg.logger.log.debug(
            'edited_cell_tree column: %s; value: %s'
            % (str(column), str(value))
        )
        cfg.logger.log.debug(
            'signature_id: %s; macroclass_id: %s'
            % (str(signature_id), str(macroclass_id))
        )
        # macroclass column
        if column == 0:
            # signature item
            if signature_id is not False:
                # get old value from table
                old_value = self.signature_catalog.table[
                    self.signature_catalog.table[
                        'signature_id'] == signature_id].macroclass_id[0]
                try:
                    value = int(value)
                except Exception as err:
                    str(err)
                    item.setData(column, old_value)
                    value = old_value
                if old_value != value:
                    if value < 0:
                        item.setData(column, old_value)
                    else:
                        # set macroclass in table
                        self.signature_catalog.table.macroclass_id[
                            self.signature_catalog.table[
                                'signature_id'] == signature_id] = value
                        # add macroclass in dictionary
                        if value not in self.signature_catalog.macroclasses:
                            self.signature_catalog.macroclasses[value] = (
                                'macroclass'
                            )
                            macroclass_color = (
                                cfg.rs.shared_tools.random_color()
                            )
                            self.signature_catalog.macroclasses_color_string[
                                value] = macroclass_color
                        # check if isolated macroclass
                        check_id = self.signature_catalog.table.macroclass_id[
                            self.signature_catalog.table[
                                'macroclass_id'] == old_value]
                        if len(check_id) == 0:
                            try:
                                del self.signature_catalog.macroclasses[
                                    old_value]
                                del self.macroclass_dock_tree[old_value]
                                cat = self.signature_catalog
                                del cat.macroclasses_color_string[old_value]
                            except Exception as err:
                                str(err)
                        # set macroclass in geometry
                        expression = '"%s" = \'%s\'' % (
                            cfg.rs.configurations.uid_field_name, signature_id
                        )
                        self.edit_vector(
                            expression=expression, field_name='macroclass_id',
                            value=value
                        )
                # set selected in table
                checked = item.checkState(0)
                if checked == 2:
                    self.signature_catalog.table.selected[
                        self.signature_catalog.table[
                            'signature_id'] == signature_id] = 1
                else:
                    self.signature_catalog.table.selected[
                        self.signature_catalog.table[
                            'signature_id'] == signature_id] = 0
                reload = True
            # macroclass item
            elif macroclass_id is not False:
                # get old value from table
                old_value = macroclass_id
                try:
                    value = int(value)
                except Exception as err:
                    str(err)
                    item.setData(column, old_value)
                    value = old_value
                if old_value != value:
                    if value < 0:
                        item.setData(column, old_value)
                        value = old_value
                    # add macroclass in dictionary
                    if value not in self.signature_catalog.macroclasses:
                        self.signature_catalog.macroclasses[value] = (
                            'macroclass'
                        )
                        macroclass_color = cfg.rs.shared_tools.random_color()
                        self.signature_catalog.macroclasses_color_string[
                            value] = macroclass_color
                    # change signature macroclass
                    self.signature_catalog.table.macroclass_id[
                        self.signature_catalog.table[
                            'macroclass_id'] == old_value] = value
                    # check if isolated macroclass
                    check_id = self.signature_catalog.table.macroclass_id[
                        self.signature_catalog.table[
                            'macroclass_id'] == old_value]
                    if len(check_id) == 0:
                        try:
                            del self.signature_catalog.macroclasses[
                                old_value]
                            del self.macroclass_dock_tree[old_value]
                            cat = self.signature_catalog
                            del cat.macroclasses_color_string[old_value]
                        except Exception as err:
                            str(err)
                    # set macroclass in geometry
                    expression = '"%s" = \'%s\'' % (
                        'macroclass_id', old_value
                    )
                    self.edit_vector(
                        expression=expression, field_name='macroclass_id',
                        value=value
                    )
                reload = True
            else:
                reload = True
        # class column
        elif column == 1:
            # signature item
            if signature_id is not False:
                # get old value from table
                old_value = self.signature_catalog.table[
                    self.signature_catalog.table[
                        'signature_id'] == signature_id].class_id[0]
                try:
                    value = int(value)
                except Exception as err:
                    str(err)
                    item.setData(column, old_value)
                    value = old_value
                if old_value != value:
                    if value < 0:
                        item.setData(column, old_value)
                    else:
                        # set class in table
                        self.signature_catalog.table.class_id[
                            self.signature_catalog.table[
                                'signature_id'] == signature_id] = value
                        # set class in geometry
                        expression = '"%s" = \'%s\'' % (
                            cfg.rs.configurations.uid_field_name, signature_id
                        )
                        self.edit_vector(
                            expression=expression, field_name='class_id',
                            value=value
                        )
                # set selected in table
                checked = item.checkState(0)
                if checked == 2:
                    self.signature_catalog.table.selected[
                        self.signature_catalog.table[
                            'signature_id'] == signature_id] = 1
                else:
                    self.signature_catalog.table.selected[
                        self.signature_catalog.table[
                            'signature_id'] == signature_id] = 0
                reload = True
        # info column
        elif column == 2:
            # signature item
            if signature_id is not False:
                # set class in table
                self.signature_catalog.table.class_name[
                    self.signature_catalog.table[
                        'signature_id'] == signature_id] = str(value)
            # macroclass item
            elif macroclass_id is not False:
                self.signature_catalog.macroclasses[
                    macroclass_id] = str(value)
        # type column
        elif column == 3:
            item.setData(column, '')
        # color column
        elif column == 4:
            item.setData(column, '')
            table.clearSelection()
        table.setSortingEnabled(True)
        table.blockSignals(False)
        if reload:
            self.roi_signature_table_tree()
        else:
            # info completer
            class_info = self.signature_catalog.table.class_name.tolist()
            macroclass_info = self.signature_catalog.macroclasses.values()
            macroclass_info_completer(macroclass_info)

    # signature table double click
    def signature_tree_double_click(self, item, column):
        table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        table.setSortingEnabled(False)
        table.blockSignals(True)
        reload = False
        # items
        try:
            signature_id = list(self.class_dock_tree.keys())[
                list(self.class_dock_tree.values()).index(item)]
            macroclass_id = False
        except Exception as err:
            str(err)
            macroclass_id = list(self.macroclass_dock_tree.keys())[
                list(self.macroclass_dock_tree.values()).index(item)]
            signature_id = False
        cfg.logger.log.debug(
            'signature_id: %s; macroclass_id: %s'
            % (str(signature_id), str(macroclass_id))
        )
        if column == 0 or column == 1 or column == 2 or column == 3:
            if macroclass_id is not False:
                item.setExpanded(not item.isExpanded())
            elif column == 2:
                expression = '"%s" = \'%s\' or ' % (
                    cfg.rs.configurations.uid_field_name, signature_id
                )
                expression = expression[:-4]
                cfg.logger.log.debug(
                    'zoom to expression: %s' % (str(expression))
                    )
                zoom_to_roi_polygons(expression)
        # color column
        elif column == 4:
            if macroclass_id is not False:
                color = cfg.util_qt.select_color()
                if color is not None:
                    self.signature_catalog.macroclasses_color_string[
                        macroclass_id] = color.toRgb().name()
                    reload = True
        table.setSortingEnabled(True)
        table.blockSignals(False)
        if reload:
            self.roi_signature_table_tree()

    # select all signatures
    def select_all_signatures(self, check=None, selected=None):
        # select all
        if check is True:
            self.all_items_set_state(1, selected)
        # unselect all
        else:
            self.all_items_set_state(0, selected)

    # set all items to state 0 or 2
    def all_items_set_state(self, value, only_selected=None):
        tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        if only_selected is False:
            # set same state for all
            self.signature_catalog.table.selected[
                self.signature_catalog.table[
                    'signature_id'] != '0'] = value
        else:
            for row in tree.selectedItems():
                # classes
                if len(row.text(1)) > 0:
                    signature = row.text(5)
                    # set selected
                    # noinspection PyUnresolvedReferences
                    self.signature_catalog.table.selected[
                        self.signature_catalog.table[
                            'signature_id'] == signature] = value
                # macroclasses
                else:
                    count = row.childCount()
                    for selected_row in range(0, count):
                        signature = row.child(selected_row).text(5)
                        # set selected
                        # noinspection PyUnresolvedReferences
                        self.signature_catalog.table.selected[
                            self.signature_catalog.table[
                                'signature_id'] == signature] = value
        self.roi_signature_table_tree()

    # change color
    def change_color(self, color):
        tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        if len(tree.selectedItems()) > 0:
            for item in tree.selectedItems():
                try:
                    signature_id = list(self.class_dock_tree.keys())[
                        list(self.class_dock_tree.values()).index(item)]
                    macroclass_id = False
                except Exception as err:
                    str(err)
                    macroclass_id = list(self.macroclass_dock_tree.keys())[
                        list(self.macroclass_dock_tree.values()).index(item)]
                    signature_id = False
                # set color in table
                # signature item
                if signature_id is not False:
                    # set color in table
                    self.signature_catalog.table.color[
                        self.signature_catalog.table[
                            'signature_id'] == signature_id] = str(
                        color.toRgb().name()
                    )
                # macroclass item
                elif macroclass_id is not False:
                    self.signature_catalog.macroclasses_color_string[
                        macroclass_id] = color.toRgb().name()
        self.roi_signature_table_tree()

    # add signature
    def add_spectral_signature_to_catalog(
            self, values, wavelengths, standard_deviations,
            macroclass_id=None, macroclass_name=None, class_id=None,
            class_name=None
    ):
        color_string = cfg.rs.shared_tools.random_color()
        unit = self.signature_catalog.bandset.get_wavelength_units()[0]
        if macroclass_id is None:
            macroclass_id = cfg.project_registry[cfg.reg_roi_macroclass_id]
        if macroclass_name is None:
            macroclass_name = cfg.project_registry[cfg.reg_roi_macroclass_name]
        if class_id is None:
            class_id = int(cfg.project_registry[cfg.reg_roi_class_id])
        if class_name is None:
            class_name = cfg.project_registry[cfg.reg_roi_class_name]
        value_list = []
        wavelength_list = []
        standard_deviation_list = []
        bandset_wavelength = self.signature_catalog.bandset.bands['wavelength']
        wavelength = numpy.array(wavelengths)
        for b in bandset_wavelength.tolist():
            arg_min = numpy.abs(wavelength - b).argmin()
            wavelength_list.append(b)
            value_list.append(values[arg_min])
            standard_deviation_list.append(standard_deviations[arg_min])
        self.signature_catalog.add_spectral_signature(
            value_list=value_list, macroclass_id=macroclass_id,
            class_id=class_id, macroclass_name=macroclass_name,
            class_name=class_name, wavelength_list=wavelength_list,
            standard_deviation_list=standard_deviation_list, geometry=0,
            signature=1, color_string=color_string, pixel_count=0,
            unit=unit
        )
        self.roi_signature_table_tree()

    # delete highlighted signatures
    def delete_selected_signatures(self):
        ids = self.get_highlighted_ids()
        for signature in ids:
            self.signature_catalog.remove_signature_by_id(
                signature_id=signature
            )

    # merge highlighted signatures
    def merge_selected_signatures(self):
        ids = self.get_highlighted_ids()
        random_color = cfg.rs.shared_tools.random_color()
        try:
            self.signature_catalog.merge_signatures_by_id(
                signature_id_list=ids, calculate_signature=True,
                macroclass_id=int(
                    cfg.project_registry[cfg.reg_roi_macroclass_id]
                ),
                class_id=int(cfg.project_registry[cfg.reg_roi_class_id]),
                macroclass_name=cfg.project_registry[
                    cfg.reg_roi_macroclass_name
                ],
                class_name=cfg.project_registry[cfg.reg_roi_class_name],
                color_string=random_color
            )
        except Exception as err:
            str(err)
            cfg.mx.msg_err_6()
            cfg.logger.log.error('signature ids: %s' % (str(ids)))

    # import spectral signature file
    def import_file(self, file_path):
        self.signature_catalog.import_file(file_path=file_path)
        self.roi_signature_table_tree()

    # import spectral signature file old version
    def import_scp_file(self, scp_file_path):
        with zipfile.ZipFile(scp_file_path) as open_file:
            for file_name in open_file.namelist():
                if file_name.endswith('.gpkg'):
                    unzip_file = open_file.open(file_name)
                    file_path = (
                        cfg.rs.configurations.temp.temporary_file_path(
                            name_suffix='.gpkg'
                        )
                    )
                    try:
                        unzip_temp_text = open(file_path, 'wb')
                        with unzip_file, unzip_temp_text:
                            # noinspection PyTypeChecker
                            shutil.copyfileobj(unzip_file, unzip_temp_text)
                        unzip_temp_text.close()
                    except Exception as err:
                        str(err)
                    break
        self.signature_catalog.import_vector(
            file_path=file_path,
            macroclass_field='MC_ID',
            macroclass_name_field='MC_name',
            class_field='C_ID', class_name_field='C_name',
            calculate_signature=True
        )
        self.roi_signature_table_tree()

    # import csv file to catalog
    def import_csv_file(self, file_path):
        random_color = cfg.rs.shared_tools.random_color()
        try:
            self.signature_catalog.import_spectral_signature_csv(
                csv_path=file_path,
                macroclass_id=int(
                    cfg.project_registry[cfg.reg_roi_macroclass_id]
                ),
                class_id=int(cfg.project_registry[cfg.reg_roi_class_id]),
                macroclass_name=cfg.project_registry[
                    cfg.reg_roi_macroclass_name],
                class_name=cfg.project_registry[cfg.reg_roi_class_name],
                color_string=random_color
            )
            self.roi_signature_table_tree()
        except Exception as err:
            str(err)
            cfg.mx.msg_err_6()
            cfg.logger.log.error('import_csv_file: %s' % (str(file_path)))

    # import vector file
    def import_vector(
            self, file_path, macroclass_field, macroclass_name_field,
            class_field, class_name_field, calculate_signature
    ):
        self.signature_catalog.import_vector(
            file_path=file_path, macroclass_field=macroclass_field,
            macroclass_name_field=macroclass_name_field,
            class_field=class_field, class_name_field=class_name_field,
            calculate_signature=calculate_signature
        )
        self.roi_signature_table_tree()

    # calculate signature of highlighted signatures
    def calculate_signature_of_selected_signatures(self):
        ids = self.get_highlighted_ids()
        for _id in ids:
            signature_array = self.signature_catalog.table[
                self.signature_catalog.table['signature_id'] == _id]
            if len(signature_array.geometry) > 0:
                geometry_check = signature_array.geometry[0]
            else:
                geometry_check = 0
            if geometry_check == 1:
                macroclass_id = signature_array.macroclass_id[0]
                class_id = signature_array.class_id[0]
                class_name = signature_array.class_name[0]
                color = signature_array.color[0]
                macroclass_name = self.signature_catalog.macroclasses[
                    macroclass_id
                ]
                try:
                    # calculate signature as merging one ROI
                    self.signature_catalog.merge_signatures_by_id(
                        signature_id_list=[_id], calculate_signature=True,
                        macroclass_id=macroclass_id, class_id=class_id,
                        macroclass_name=macroclass_name, class_name=class_name,
                        color_string=color
                    )
                    # remove original signature
                    self.signature_catalog.remove_signature_by_id(
                        signature_id=_id
                    )
                except Exception as err:
                    cfg.mx.msg_err_6()
                    cfg.logger.log.error('signature id: %s; %s'
                                         % (str(_id), str(err)))

    # get highlighted IDs
    def get_highlighted_ids(self, select_all=None, signatures=None):
        tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        if select_all is True:
            # get only signature
            if signatures is True:
                ids = self.signature_catalog.table.signature_id[
                    self.signature_catalog.table['signature'] == 1
                    ].tolist()
            else:
                ids = self.signature_catalog.table.signature_id.tolist()
        else:
            ids = []
            for row in tree.selectedItems():
                # classes
                if len(row.text(1)) > 0:
                    signature = row.text(5)
                    # set selected
                    # noinspection PyUnresolvedReferences
                    ids.append(
                        self.signature_catalog.table.signature_id[
                            self.signature_catalog.table[
                                'signature_id'] == signature][0].item()
                    )
                # macroclasses
                else:
                    count = row.childCount()
                    for selected_row in range(0, count):
                        signature = row.child(selected_row).text(5)
                        # set selected
                        # noinspection PyUnresolvedReferences
                        ids.append(
                            self.signature_catalog.table.signature_id[
                                self.signature_catalog.table[
                                    'signature_id'] == signature][0].item()
                        )
        cfg.logger.log.debug('get_highlighted_ids: %s' % (str(ids)))
        return ids

    # collapse menu
    def collapse(self):
        if self.collapse_tree:
            tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
            tree.collapseAll()
            self.collapse_tree = False
        else:
            tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
            tree.expandAll()
            self.collapse_tree = True



""" Interface functions """


# reset input
# noinspection PyTypeChecker
def reset_input():
    answer = cfg.util_qt.question_box(
        QApplication.translate('semiautomaticclassificationplugin',
                               'Remove training input'),
        QApplication.translate(
            'semiautomaticclassificationplugin',
            'Are you sure you want to remove training input?'
        )
    )
    if answer is True:
        reset_input_dock()


# reset input
def reset_input_dock():
    cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(False)
    cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
    if cfg.scp_training is not None:
        cfg.scp_training.reset_signature_catalog()
    cfg.scp_training = None


# calculate signatures
# noinspection PyTypeChecker
def calculate_signatures():
    ids = cfg.scp_training.get_highlighted_ids(select_all=False)
    if len(ids) == 0:
        return 0
    answer = cfg.util_qt.question_box(
        QApplication.translate('semiautomaticclassificationplugin',
                               'Calculate signatures'),
        QApplication.translate('semiautomaticclassificationplugin',
                               'Calculate signatures for highlighted items?')
    )
    if answer is True:
        # save previous catalog file
        cfg.scp_training.save_temporary_signature_catalog()
        signature_catalog = cfg.scp_training.signature_catalog_copy()
        cfg.scp_training.set_signature_catalog(
            signature_catalog=signature_catalog
        )
        cfg.ui_utils.add_progress_bar()
        cfg.scp_training.calculate_signature_of_selected_signatures()
        cfg.ui_utils.remove_progress_bar(sound=False)
        cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
        cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
        # create table tree
        cfg.scp_training.roi_signature_table_tree()
        # save training input
        if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
            cfg.scp_training.save_signature_catalog()
    return None


# merge highlighted signatures
# noinspection PyTypeChecker
def merge_signatures():
    table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    selected = table.selectedItems()
    if len(selected) > 0:
        answer = cfg.util_qt.question_box(
            QApplication.translate('semiautomaticclassificationplugin',
                                   'Merge signatures'),
            '%s MC ID: %s and C ID:%s?' % (
                QApplication.translate('semiautomaticclassificationplugin',
                                       'Merge highlighted signatures into'),
                cfg.project_registry[cfg.reg_roi_class_id],
                cfg.project_registry[cfg.reg_roi_macroclass_id],
            )
        )
        if answer is True:
            # save previous catalog file
            cfg.scp_training.save_temporary_signature_catalog()
            signature_catalog = cfg.scp_training.signature_catalog_copy()
            cfg.scp_training.set_signature_catalog(
                signature_catalog=signature_catalog
            )
            cfg.ui_utils.add_progress_bar()
            cfg.scp_training.merge_selected_signatures()
            cfg.ui_utils.remove_progress_bar(sound=False)
            cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
            cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
            # create table tree
            cfg.scp_training.roi_signature_table_tree()
            # save training input
            if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
                cfg.scp_training.save_signature_catalog()


# remove selected signatures
# noinspection PyTypeChecker
def remove_selected_signatures():
    table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    selected = table.selectedItems()
    if len(selected) > 0:
        answer = cfg.util_qt.question_box(
            QApplication.translate('semiautomaticclassificationplugin',
                                   'Delete signatures'),
            QApplication.translate(
                'semiautomaticclassificationplugin',
                'Are you sure you want to delete highlighted ROIs '
                'and signatures?'
            )
        )
        if answer is True:
            # save previous catalog file
            cfg.scp_training.save_temporary_signature_catalog()
            signature_catalog = cfg.scp_training.signature_catalog_copy()
            cfg.scp_training.set_signature_catalog(
                signature_catalog=signature_catalog
            )
            cfg.scp_training.delete_selected_signatures()
            cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
            cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
            # create table tree
            cfg.scp_training.roi_signature_table_tree()
            # save training input
            if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
                cfg.scp_training.save_signature_catalog()


# delete the selected classes with all their ROIs (Delete Class button)
# noinspection PyTypeChecker
def delete_selected_classes():
    if cfg.scp_training is None or cfg.scp_training.signature_catalog is None:
        cfg.mx.msg_war_5()
        return
    tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    class_ids = []
    for row in tree.selectedItems():
        # class item or ROI item: column 0 holds the class number
        value = row.text(0)
        try:
            value = int(value)
        except ValueError:
            continue
        if value not in class_ids:
            class_ids.append(value)
    if not class_ids:
        _roi_message('Select the class to delete in the list.',
                     Qgis.MessageLevel.Warning)
        return
    names = ', '.join(
        '%s (%s)' % (i, cfg.scp_training.signature_catalog.macroclasses.get(
            i, '')) for i in class_ids)
    answer = cfg.util_qt.question_box(
        QApplication.translate('semiautomaticclassificationplugin',
                               'Delete class'),
        QApplication.translate(
            'semiautomaticclassificationplugin',
            'Are you sure you want to delete the class %s and all its ROIs?'
        ) % names
    )
    if answer is not True:
        return
    cfg.ui_utils.add_progress_bar()
    # save previous catalog file
    cfg.scp_training.save_temporary_signature_catalog()
    signature_catalog = cfg.scp_training.signature_catalog_copy()
    cfg.scp_training.set_signature_catalog(signature_catalog=signature_catalog)
    catalog = cfg.scp_training.signature_catalog
    try:
        for class_id in class_ids:
            table = catalog.table
            if table is not None:
                ids = table.signature_id[
                    table['macroclass_id'] == class_id].tolist()
                for signature_id in ids:
                    catalog.remove_signature_by_id(signature_id=signature_id)
            # a class without ROIs is removed from the lists too
            catalog.macroclasses.pop(class_id, None)
            catalog.macroclasses_color_string.pop(class_id, None)
    except Exception as err:
        cfg.logger.log.error(str(err))
        cfg.mx.msg_err_6()
    cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
    cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
    cfg.scp_training.roi_signature_table_tree()
    if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
        cfg.scp_training.save_signature_catalog()
    cfg.ui_utils.remove_progress_bar(sound=False)


# zoom to clicked ROI
def zoom_to_roi_polygons(expression):
    if cfg.scp_training is not None:
        cfg.map_canvas.setRenderFlag(False)
        zoom_to_selected(cfg.scp_training.layer, expression)
        cfg.util_qgis.set_layer_visible(cfg.scp_training.layer, True)
        cfg.util_qgis.move_layer_to_top(cfg.scp_training.layer)
        cfg.map_canvas.setRenderFlag(True)


# Zoom to selected feature of layer
def zoom_to_selected(layer, expression):
    layer.removeSelection()
    layer.selectByExpression(expression)
    cfg.map_canvas.zoomToSelected(layer)
    layer.removeSelection()




# properties menu
def properties_menu():
    add_signature_to_spectral_plot(1)


# collapse menu
def collapse_menu():
    cfg.scp_training.collapse()


# change macroclass menu
# noinspection PyTypeChecker
def change_macroclass_menu():
    dock_tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    if len(dock_tree.selectedItems()) > 0:
        answer = cfg.util_qt.question_box(
            QApplication.translate('semiautomaticclassificationplugin',
                                   'Change Macroclass ID'),
            QApplication.translate(
                'semiautomaticclassificationplugin',
                'Change the Macroclass ID for highlighted items to'
            )
            + ' %s ?' % str(cfg.project_registry[cfg.reg_roi_macroclass_id])
        )
        if answer is True:
            cfg.scp_training.edit_macroclass(
                cfg.project_registry[cfg.reg_roi_macroclass_id]
            )
            cfg.scp_training.roi_signature_table_tree()


# change color menu
def change_color_menu():
    color = cfg.util_qt.select_color()
    if color is not None:
        cfg.scp_training.change_color(color)


# clear selection menu
def clear_selection_menu():
    table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    table.clearSelection()


# zoom to menu
def zoom_to_menu():
    ids = cfg.scp_training.get_highlighted_ids(
        select_all=False, signatures=False
    )
    expression = ''
    for _id in ids:
        expression += '"%s" = \'%s\' or ' % (
            cfg.rs.configurations.uid_field_name, _id
        )
    expression = expression[:-4]
    cfg.logger.log.debug('zoom_to_menu expression: %s' % (str(expression)))
    zoom_to_roi_polygons(expression)


# select all menu
def select_all_menu():
    checked = None
    table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    if len(table.selectedItems()) > 0:
        selected = True
        items = table.selectedItems()
    else:
        selected = False
        items = []
        checked = cfg.scp_training.signature_catalog.table.selected[0]
    # get check value
    for i in items:
        # classes
        if len(i.text(1)) > 0:
            checked = i.checkState(0)
        # macroclasses
        else:
            count = i.childCount()
            for r in range(0, count):
                checked = i.child(r).checkState(0)
        break
    if checked == 2 or checked == 1:
        cfg.scp_training.select_all_signatures(check=False, selected=selected)
    elif checked == 0:
        cfg.scp_training.select_all_signatures(check=True, selected=selected)




""" Context menu """


# add item to menu
def add_menu_item(menu, function, icon_name, name, tooltip=''):
    try:
        action = QAction(
            QIcon(
                ':/plugins/raster_classification/icons/%s'
                % icon_name
            ), name, cfg.iface.mainWindow()
        )
    except Exception as err:
        str(err)
        action = QAction(name, cfg.iface.mainWindow())
    action.setObjectName('action')
    action.setToolTip(tooltip)
    # noinspection PyUnresolvedReferences
    action.triggered.connect(function)
    menu.addAction(action)
    return action


# menu
# noinspection PyTypeChecker
def context_menu(event):
    menu = QMenu()
    menu.setToolTipsVisible(True)
    add_menu_item(
        menu, zoom_to_menu,
        'raster_classification_zoom_to_ROI.svg',
        QApplication.translate('semiautomaticclassificationplugin', 'Zoom to')
    )
    add_menu_item(
        menu, select_all_menu,
        'raster_classification_options.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Check/uncheck')
    )
    add_menu_item(
        menu, clear_selection_menu,
        'raster_classification_select_all.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Clear selection')
    )
    add_menu_item(
        menu, collapse_menu, 'raster_classification_docks.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Collapse/expand all')
    )
    menu.addSeparator()
    add_menu_item(
        menu, change_macroclass_menu,
        'raster_classification_enter.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Change MC ID')
    )
    add_menu_item(
        menu, change_color_menu, 'raster_classification_enter.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Change color')
    )
    menu.addSeparator()
    add_menu_item(
        menu, merge_signatures,
        'raster_classification_merge_sign_tool.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Merge items')
    )
    add_menu_item(
        menu, calculate_signatures,
        'raster_classification_add_sign_tool.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Calculate signatures')
    )
    add_menu_item(
        menu, remove_selected_signatures,
        'raster_classification_remove.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Delete items')
    )
    menu.addSeparator()
    add_menu_item(
        menu, add_signature_to_spectral_plot,
        'raster_classification_sign_tool.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Add to spectral plot')
    )
    add_menu_item(
        menu, properties_menu,
        'raster_classification_accuracy_tool.svg',
        QApplication.translate('semiautomaticclassificationplugin',
                               'Properties')
    )
    menu.addSeparator()
    add_menu_item(
        menu, cfg.input_interface.import_signatures_tab,
        'raster_classification_import_spectral_library.svg',
        QApplication.translate('semiautomaticclassificationplugin', 'Import')
    )
    add_menu_item(
        menu, cfg.input_interface.export_signatures_tab,
        'raster_classification_export_spectral_library.svg',
        QApplication.translate('semiautomaticclassificationplugin', 'Export')
    )
    table = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
    menu.exec(table.mapToGlobal(event))


""" Toolbar functions """














# Activate pointer for ROI creation
def pointer_manual_roi_active():
    cfg.roi_points = []
    cfg.qgis_vertex_item_list = []
    cfg.map_canvas.setMapTool(cfg.manual_roi_pointer)
    cursor = QCursor()
    cursor.setShape(Qt.CursorShape.CrossCursor)
    cfg.map_canvas.setCursor(cursor)
    _roi_message(
        'Polygon: left click adds a vertex, right click closes the polygon '
        'and adds it to the class.'
    )
















# ROI macroclass ID
def roi_macroclass_id_value():
    value = cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_ID_spin.value()
    cfg.project_registry[cfg.reg_roi_macroclass_id] = value
    # set macroclass name if existing
    if cfg.scp_training is not None:
        if value in cfg.scp_training.signature_catalog.macroclasses:
            macroclass = cfg.scp_training.signature_catalog.macroclasses[value]
            cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_line.setText(
                macroclass
            )
            cfg.project_registry[cfg.reg_roi_macroclass_name] = macroclass


def roi_macroclass_name_info():
    cfg.project_registry[cfg.reg_roi_macroclass_name] = str(
        cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_line.text()
    )








# macroclass info completer
def macroclass_info_completer(macroclass_list):
    # class names
    completer_macroclass_name = QCompleter(macroclass_list)
    cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_line.setCompleter(
        completer_macroclass_name
    )






""" Map functions """


# add roi polygon
def add_roi_polygon_to_map(source_layer, feature_id):
    color = QColor(cfg.qgis_registry[cfg.reg_roi_color])
    try:
        value = 255 - int(
            int(cfg.qgis_registry[cfg.reg_roi_transparency]) * 255 / 100
        )
        color.setAlpha(value)
    except Exception as err:
        str(err)
        color.setAlpha(100)
    feature = cfg.util_qgis.get_feature_by_id(source_layer, feature_id)
    cfg.roi_map_polygon = QgsHighlight(
        cfg.map_canvas, feature.geometry(), source_layer
    )
    cfg.roi_map_polygon.setWidth(2)
    cfg.roi_map_polygon.setColor(QColor('#53d4e7'))
    try:
        cfg.roi_map_polygon.setFillColor(color)
    except Exception as err:
        str(err)
    cfg.map_canvas.refresh()
    cfg.roi_map_polygon.show()
    cfg.ctrl_click = None


# clear scp dock rubber
def clear_scp_dock_rubber():
    for point in cfg.roi_points:
        try:
            cfg.map_canvas.scene().removeItem(point)
        except Exception as err:
            str(err)
    cfg.roi_points = []
    cfg.scp_dock_rubber_roi.hide()
    cfg.scp_dock_rubber_roi.reset()
    if cfg.roi_map_polygon is not None:
        cfg.roi_map_polygon.hide()
    if cfg.roi_map_polygon is not None:
        cfg.map_canvas.scene().removeItem(cfg.roi_map_polygon)
        cfg.roi_map_polygon = None
    for point in cfg.qgis_vertex_item_list:
        cfg.map_canvas.scene().removeItem(point)
        del point
    if cfg.roi_center_vertex is not None:
        cfg.roi_center_vertex.hide()
    cfg.qgis_vertex_item_list = []
    cfg.map_canvas.refresh()


""" Training input functions """


# Save last ROI to training
def save_roi_to_training(bandset_number=None):
    # bandset_number is False when triggered by action
    if bandset_number is None or bandset_number is False:
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    if cfg.scp_training is None or cfg.scp_training.signature_catalog is None:
        cfg.mx.msg_war_5()
        return False
    elif cfg.temporary_roi is None:
        cfg.mx.msg_war_4()
        return None
    else:
        cfg.ui_utils.add_progress_bar()
        # get vector from ROI
        roi_path = cfg.rs.configurations.temp.temporary_file_path(
            name_suffix='.gpkg'
        )
        cfg.util_qgis.save_memory_layer_to_geopackage(
            cfg.temporary_roi, roi_path
        )
        # calculate signature
        if cfg.project_registry[cfg.reg_signature_calculation_check] == 2:
            calculate_signature = True
        else:
            calculate_signature = False
        cfg.logger.log.debug(
            'bandset number: %s; bandset catalog: %s; '
            'bandset count: %s; bandset: %s'
            % (str(bandset_number), str(cfg.bandset_catalog),
               str(cfg.bandset_catalog.get_bandset_count()),
               str(cfg.bandset_catalog.get(bandset_number))
               )
        )
        # save previous catalog file
        cfg.scp_training.save_temporary_signature_catalog()
        signature_catalog = cfg.scp_training.signature_catalog_copy()
        class_name = cfg.project_registry[cfg.reg_roi_macroclass_name]
        macroclass_name = cfg.project_registry[cfg.reg_roi_macroclass_name]
        # save roi to new catalog
        try:
            signature_catalog.import_vector(
                file_path=roi_path, macroclass_value=int(
                    cfg.project_registry[cfg.reg_roi_macroclass_id]
                ),
                class_value=int(cfg.project_registry[cfg.reg_roi_class_id]),
                macroclass_name=macroclass_name, class_name=class_name,
                calculate_signature=calculate_signature
            )
            if cfg.rs.configurations.action:
                cfg.scp_training.set_signature_catalog(
                    signature_catalog=signature_catalog
                )
                clear_scp_dock_rubber()
                cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(
                    True
                )
                cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(
                    False
                )
                cfg.project_registry[cfg.reg_roi_class_id] = int(
                    cfg.project_registry[cfg.reg_roi_class_id]) + 1
                # create table tree
                cfg.scp_training.roi_signature_table_tree()
                # save training input
                if (cfg.project_registry[cfg.reg_save_training_input_check]
                        == 2):
                    cfg.scp_training.save_signature_catalog()
        except Exception as err:
            cfg.logger.log.error(str(err))
        cfg.ui_utils.remove_progress_bar(sound=False)
        return None


# undo training modifications
# noinspection PyTypeChecker
def undo_saved_roi():
    answer = cfg.util_qt.question_box(
        QApplication.translate('semiautomaticclassificationplugin',
                               'Undo save ROI'),
        QApplication.translate('semiautomaticclassificationplugin',
                               'Are you sure you want to undo?')
    )
    if answer is True:
        cfg.logger.log.debug('undo')
        # training input undo
        cfg.scp_training.undo()
        # save training input
        if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
            cfg.scp_training.save_signature_catalog()


# restore training buffered
# noinspection PyTypeChecker
def redo_saved_roi():
    answer = cfg.util_qt.question_box(
        QApplication.translate('semiautomaticclassificationplugin',
                               'Redo save ROI'),
        QApplication.translate('semiautomaticclassificationplugin',
                               'Are you sure you want to redo?')
    )
    if answer is True:
        cfg.logger.log.debug('redo')
        # training input redo
        cfg.scp_training.redo()
        # save training input
        if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
            cfg.scp_training.save_signature_catalog()


# left click
def left_click_manual(point):
    qgis_crs = cfg.util_qgis.get_qgis_crs()
    point = cfg.utils.check_point_in_image(point=point, output_crs=qgis_crs)
    if point is False:
        cfg.mx.msg_war_3()
        return False
    time = cfg.utils.get_time()
    name = '%s%s' % (cfg.temp_roi_name, time)
    # crs
    bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get(bandset_number)
    band_count = bandset_x.get_band_count()
    if band_count == 0:
        return False
    memory_layer = cfg.util_qgis.add_vector_layer(
        'MultiPolygon?crs=%s' % qgis_crs.toWkt(), name, 'memory'
    )
    memory_layer.setCrs(qgis_crs)
    cfg.roi_points.append(point)
    # rubber band polygon to store vertices
    cfg.scp_dock_rubber_roi.addPoint(point)
    geometry = cfg.scp_dock_rubber_roi.asGeometry()
    vertex = QgsVertexMarker(cfg.map_canvas)
    vertex.setCenter(point)
    cfg.qgis_vertex_item_list.append(vertex)
    cfg.scp_dock_rubber_roi.setToGeometry(geometry, qgis_crs)
    cfg.scp_dock_rubber_roi.show()
    return None


# right click
def right_click_manual(point):
    qgis_crs = cfg.util_qgis.get_qgis_crs()
    left_click_manual(point)
    feature = QgsFeature()
    time = cfg.utils.get_time()
    name = '%s%s' % (cfg.temp_roi_name, time)
    # crs
    bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get(bandset_number)
    band_count = bandset_x.get_band_count()
    if band_count == 0:
        return False
    memory_layer = cfg.util_qgis.add_vector_layer(
        'MultiPolygon?crs=%s' % qgis_crs.toWkt(), name, 'memory'
    )
    memory_layer.setCrs(qgis_crs)
    if not len(cfg.roi_points) >= 3:
        cfg.mx.msg_inf_2()
        clear_scp_dock_rubber()
        return None
    q_point = QPointF()
    f_polygon = QPolygonF()
    for v in cfg.roi_points:
        q_point.setX(v.x())
        q_point.setY(v.y())
        f_polygon.append(q_point)
    q_point.setX(cfg.roi_points[0].x())
    q_point.setY(cfg.roi_points[0].y())
    f_polygon.append(q_point)
    q_geometry = QgsGeometry().fromQPolygonF(f_polygon)
    memory_layer.addTopologicalPoints(q_geometry)
    data_provider = memory_layer.dataProvider()
    # create temp ROI
    memory_layer.startEditing()
    # add fields
    data_provider.addAttributes(
        [QgsField(cfg.empty_field_name, QMetaType.Type.Int)]
    )
    # add a feature
    if cfg.ctrl_click is not None:
        q_geometry = add_part_to_roi(q_geometry)
    feature.setGeometry(q_geometry)
    feature.setAttributes([1])
    data_provider.addFeatures([feature])
    memory_layer.commitChanges()
    memory_layer.updateExtents()
    cfg.temporary_roi = memory_layer
    clear_scp_dock_rubber()
    add_roi_polygon_to_map(cfg.temporary_roi, 1)
    add_roi_to_class()
    return None


# Create button: available only when the class does not exist yet; the
# classes are unique (by number and by name)
def update_create_button(*_args):
    try:
        ui = cfg.dock_class_simpl_dlg.ui
        name = str(ui.ROI_Macroclass_line.text()).strip()
        class_id = int(ui.ROI_Macroclass_ID_spin.value())
        enabled = bool(name)
        tip = 'Create the class (number and name) that receives the ROIs'
        catalog = None
        if cfg.scp_training is not None:
            catalog = cfg.scp_training.signature_catalog
        if catalog is not None and catalog.macroclasses:
            if class_id in catalog.macroclasses:
                enabled = False
                tip = ('The class %s already exists: change the number to '
                       'create another class' % class_id)
            elif name.casefold() in [
                    str(n).casefold() for n in catalog.macroclasses.values()]:
                enabled = False
                tip = 'This class name is already used: choose another name'
        ui.button_Save_ROI.setEnabled(enabled)
        ui.button_Save_ROI.setToolTip(tip)
    except Exception as err:
        cfg.logger.log.error(str(err))


# a class or a ROI selected in the list becomes the class of the new ROIs
def select_class_from_tree():
    try:
        tree = cfg.dock_class_simpl_dlg.ui.signature_list_treeWidget
        item = tree.currentItem()
        if item is None or not item.isSelected():
            return
        class_id = int(item.text(0))
        spin = cfg.dock_class_simpl_dlg.ui.ROI_Macroclass_ID_spin
        if spin.value() != class_id:
            spin.setValue(class_id)
        else:
            update_create_button()
    except Exception as err:
        cfg.logger.log.error(str(err))


# message of the ROI tools
def _roi_message(text, level=None):
    cfg.iface.messageBar().pushMessage(
        'Raster Classification', tr(text),
        level=Qgis.MessageLevel.Info if level is None else level, duration=8
    )


# create a class (Save button of the simplified panel): the class gets an ID
# and a name, the ROIs drawn afterwards are added to it
def create_class():
    if cfg.scp_training is None or cfg.scp_training.signature_catalog is None:
        # no training input yet: ask where to create it, then go on
        _roi_message('No training file yet: choose where to create it.')
        create_training_input()
        if (cfg.scp_training is None
                or cfg.scp_training.signature_catalog is None):
            return False
    ui = cfg.dock_class_simpl_dlg.ui
    class_id = int(ui.ROI_Macroclass_ID_spin.value())
    name = str(ui.ROI_Macroclass_line.text()).strip()
    if not name:
        _roi_message('Enter a name for the class.', Qgis.MessageLevel.Warning)
        return False
    catalog = cfg.scp_training.signature_catalog
    if class_id in catalog.macroclasses:
        _roi_message(tr('The class %s already exists: each class is '
                        'unique.') % class_id, Qgis.MessageLevel.Warning)
        update_create_button()
        return False
    if name.casefold() in [
            str(n).casefold() for n in catalog.macroclasses.values()]:
        _roi_message(tr('A class named "%s" already exists: each class '
                        'is unique.') % name, Qgis.MessageLevel.Warning)
        update_create_button()
        return False
    cfg.project_registry[cfg.reg_roi_macroclass_id] = class_id
    cfg.project_registry[cfg.reg_roi_macroclass_name] = name
    catalog.macroclasses[class_id] = name
    if class_id not in catalog.macroclasses_color_string:
        catalog.macroclasses_color_string[class_id] = (
            cfg.rs.shared_tools.random_color()
        )
    cfg.scp_training.roi_signature_table_tree()
    if cfg.project_registry[cfg.reg_save_training_input_check] == 2:
        cfg.scp_training.save_signature_catalog()
    _roi_message(
        tr('Class %s (%s) created: draw its ROIs with Polygon or Circle, the '
           'right click adds each ROI to it. For another class, change the '
           'number and the name, then Save.') % (class_id, name)
    )
    return True


# add the ROI just drawn to the class chosen in the panel
def add_roi_to_class():
    ui = cfg.dock_class_simpl_dlg.ui
    ok = cfg.scp_training is not None
    class_id = int(ui.ROI_Macroclass_ID_spin.value())
    catalog = None
    if ok:
        catalog = cfg.scp_training.signature_catalog
        ok = catalog is not None and class_id in catalog.macroclasses
    if not ok:
        clear_scp_dock_rubber()
        cfg.temporary_roi = None
        _roi_message(
            'Create the class first: enter its number and name, then click '
            'Save. The ROI was not added.', Qgis.MessageLevel.Warning
        )
        return False
    # use the registered name of the class
    cfg.project_registry[cfg.reg_roi_macroclass_id] = class_id
    cfg.project_registry[cfg.reg_roi_macroclass_name] = (
        catalog.macroclasses[class_id]
    )
    save_roi_to_training()
    return True


_circle = {'center': None}


# Activate pointer for circular ROI creation
def pointer_circle_roi_active():
    _circle['center'] = None
    cfg.roi_points = []
    cfg.qgis_vertex_item_list = []
    cfg.map_canvas.setMapTool(cfg.circle_roi_pointer)
    cursor = QCursor()
    cursor.setShape(Qt.CursorShape.CrossCursor)
    cfg.map_canvas.setCursor(cursor)
    _roi_message(
        'Circle: left click sets the center, move the cursor, right click '
        'sets the radius and adds the circle to the class (Esc cancels).'
    )


def cancel_circle_roi():
    _circle['center'] = None
    clear_scp_dock_rubber()


# circle: left click = center
def left_click_circle(point):
    qgis_crs = cfg.util_qgis.get_qgis_crs()
    point = cfg.utils.check_point_in_image(point=point, output_crs=qgis_crs)
    if point is False:
        cfg.mx.msg_war_3()
        return False
    clear_scp_dock_rubber()
    _circle['center'] = QgsPointXY(point)
    vertex = QgsVertexMarker(cfg.map_canvas)
    vertex.setCenter(point)
    cfg.qgis_vertex_item_list.append(vertex)
    return None


def _circle_geometry(center, point):
    radius = center.distance(QgsPointXY(point))
    if radius <= 0:
        return None
    return QgsGeometry.fromPointXY(center).buffer(radius, 48)


# circle: the cursor moves = radius
def moved_circle(point):
    center = _circle['center']
    if center is None:
        return
    geometry = _circle_geometry(center, point)
    if geometry is None:
        return
    ring = geometry.asPolygon()[0]
    cfg.scp_dock_rubber_roi.setToGeometry(
        QgsGeometry.fromPolylineXY(ring), cfg.util_qgis.get_qgis_crs()
    )
    cfg.scp_dock_rubber_roi.show()


# circle: right click = radius, the circle is closed and added to the class
def right_click_circle(point):
    center = _circle['center']
    if center is None:
        _roi_message('Left click first to set the center of the circle.',
                     Qgis.MessageLevel.Warning)
        return None
    geometry = _circle_geometry(center, point)
    if geometry is None:
        return None
    qgis_crs = cfg.util_qgis.get_qgis_crs()
    bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get(bandset_number)
    if bandset_x is None or bandset_x.get_band_count() == 0:
        return False
    name = '%s%s' % (cfg.temp_roi_name, cfg.utils.get_time())
    memory_layer = cfg.util_qgis.add_vector_layer(
        'MultiPolygon?crs=%s' % qgis_crs.toWkt(), name, 'memory'
    )
    memory_layer.setCrs(qgis_crs)
    geometry.convertToMultiType()
    data_provider = memory_layer.dataProvider()
    memory_layer.startEditing()
    data_provider.addAttributes(
        [QgsField(cfg.empty_field_name, QMetaType.Type.Int)]
    )
    feature = QgsFeature()
    feature.setGeometry(geometry)
    feature.setAttributes([1])
    data_provider.addFeatures([feature])
    memory_layer.commitChanges()
    memory_layer.updateExtents()
    cfg.temporary_roi = memory_layer
    _circle['center'] = None
    clear_scp_dock_rubber()
    add_roi_polygon_to_map(cfg.temporary_roi, 1)
    add_roi_to_class()
    return None


# add multipart ROI
def add_part_to_roi(part):
    if cfg.temporary_roi is not None and cfg.ctrl_click is True:
        features = cfg.temporary_roi.getFeatures()
        feature = QgsFeature()
        features.nextFeature(feature)
        geometry = QgsGeometry(feature.geometry())
        geometry.convertToMultiType()
        part.convertToMultiType()
        geometry.addPartGeometry(part)
        cfg.second_temporary_roi = cfg.temporary_roi
        return geometry
    else:
        return part


def delete_last_roi():
    cfg.temporary_roi = cfg.second_temporary_roi
    try:
        add_roi_polygon_to_map(cfg.temporary_roi, 1)
    except Exception as err:
        str(err)












""" Training input """


# Create new input
# noinspection PyTypeChecker
def create_training_input():
    output_path = cfg.util_qt.get_save_file_name(
        None, QApplication.translate('semiautomaticclassificationplugin',
                                     'Create training input'),
        '', '*.scpx', 'scpx'
    )
    if output_path is not False:
        if output_path.lower().endswith('.scpx'):
            pass
        elif not output_path.lower().endswith('.scpx'):
            output_path += '.scpx'
        reset_input_dock()
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
        cfg.project_registry[cfg.reg_training_bandset_number] = bandset_number
        bandset_x = cfg.bandset_catalog.get(bandset_number)
        band_count = bandset_x.get_band_count()
        cfg.logger.log.debug('bandset band count: %s' % (str(band_count)))
        if band_count == 0:
            cfg.mx.msg_war_6(bandset_number)
            return
        signature_catalog = cfg.rs.spectral_signatures_catalog(
            bandset=cfg.bandset_catalog.get(bandset_number)
        )
        # load vector in QGIS
        cfg.scp_training = TrainingVectorLayer(
            signature_catalog=signature_catalog, output_path=output_path
        )
        cfg.scp_training.save_signature_catalog()


# import training file
# noinspection PyTypeChecker
def import_library_file(path=None):
    if path is None or path is False:
        file_path = cfg.util_qt.get_open_file(
            None, QApplication.translate('semiautomaticclassificationplugin',
                                         'Select a training input'), '',
            'Signature catalog package (*.scpx);; '
            'Signature catalog package old version (*.scp);;'
            'USGS library (*.zip);;ASTER library (*.txt);;CSV file (*.csv)'
        )
    else:
        file_path = path
    if len(file_path) > 0:
        cfg.ui_utils.add_progress_bar()
        # save previous catalog file
        cfg.scp_training.save_temporary_signature_catalog()
        signature_catalog = cfg.scp_training.signature_catalog_copy()
        cfg.scp_training.set_signature_catalog(
            signature_catalog=signature_catalog
        )
        if file_path.endswith('.scpx'):
            cfg.scp_training.import_file(file_path)
        elif file_path.endswith('.scp'):
            cfg.scp_training.import_scp_file(file_path)
        elif file_path.endswith('.zip'):
            cfg.signature_importer.import_usgs_library(file_path)
        elif file_path.endswith('.csv'):
            cfg.scp_training.import_csv_file(file_path)
        elif file_path.endswith('.txt'):
            cfg.signature_importer.aster_library(file_path)
        cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
        cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
        cfg.ui_utils.remove_progress_bar(sound=False)


# open training file
# noinspection PyTypeChecker
def open_training_input_file(path=None):
    if path is None or path is False:
        file_path = cfg.util_qt.get_open_file(
            None, QApplication.translate('semiautomaticclassificationplugin',
                                         'Select a training input'), '',
            'Signature catalog package (*.scpx)'
        )
    else:
        file_path = path
    if len(file_path) > 0:
        open_signature_catalog_file(file_path)


# open signature file
# noinspection PyTypeChecker
def open_signature_catalog_file(file_path=None, bandset_number=None):
    cfg.logger.log.info('open_signature_catalog_file: %s' % (str(file_path)))
    if bandset_number is None:
        bandset_number = cfg.project_registry[cfg.reg_active_bandset_number]
    bandset_x = cfg.bandset_catalog.get(bandset_number)
    if bandset_x is None:
        cfg.mx.msg_war_6(bandset_number)
        return
    band_count = bandset_x.get_band_count()
    cfg.project_registry[cfg.reg_training_bandset_number] = bandset_number
    cfg.logger.log.debug('bandset band count: %s' % (str(band_count)))
    if band_count == 0:
        cfg.mx.msg_war_6(bandset_number)
    # copy file to temporary file
    temp_path = cfg.rs.configurations.temp.temporary_file_path(
        name_suffix='.scpx'
    )
    cfg.rs.files_directories.copy_file(file_path, temp_path)
    signature_catalog = cfg.rs.spectral_signatures_catalog(
        bandset=cfg.bandset_catalog.get(bandset_number)
    )
    signature_catalog.load(file_path=temp_path)
    # remove training input
    project = cfg.util_qgis.get_qgis_project()
    if cfg.scp_training is not None:
        try:
            project.removeMapLayer(cfg.scp_training.layer)
        except Exception as err:
            str(err)
    # load vector in QGIS
    cfg.scp_training = TrainingVectorLayer(
        signature_catalog=signature_catalog, output_path=file_path
    )


# export signature to vector
# noinspection PyTypeChecker
def export_signature_vector():
    output_path = cfg.util_qt.get_save_file_name(
        None, QApplication.translate('semiautomaticclassificationplugin',
                                     'Export training input'),
        '', 'SHP file (*.shp);;GPKG file (*.gpkg)'
    )
    if output_path is not False:
        if str(output_path).endswith('.shp'):
            vector_format = 'ESRI Shapefile'
        elif str(output_path).endswith('.gpkg'):
            vector_format = 'GPKG'
        else:
            output_path += '.gpkg'
            vector_format = 'GPKG'
        ids = cfg.scp_training.get_highlighted_ids()
        if len(ids) > 0:
            cfg.ui_utils.add_progress_bar()
            cfg.scp_training.signature_catalog.export_vector(
                signature_id_list=ids, output_path=output_path,
                vector_format=vector_format
            )
            cfg.ui_utils.remove_progress_bar(sound=False)
            cfg.mx.msg_inf_4()
        else:
            ids = cfg.scp_training.get_highlighted_ids(select_all=True)
            if len(ids) > 0:
                cfg.ui_utils.add_progress_bar()
                cfg.scp_training.signature_catalog.export_vector(
                    signature_id_list=ids, output_path=output_path,
                    vector_format=vector_format
                )
                cfg.ui_utils.remove_progress_bar(sound=False)
                cfg.mx.msg_inf_4()


# export signature file
# noinspection PyTypeChecker
def export_signature_file():
    output_path = cfg.util_qt.get_save_file_name(
        None, QApplication.translate('semiautomaticclassificationplugin',
                                     'Export training input'),
        '', 'Training file (*.scpx)'
    )
    if output_path is not False:
        if output_path.lower().endswith('.scpx'):
            pass
        elif not output_path.lower().endswith('.scpx'):
            output_path += '.scpx'
        ids = cfg.scp_training.get_highlighted_ids()
        if len(ids) > 0:
            cfg.ui_utils.add_progress_bar()
            cfg.scp_training.save_signature_catalog(
                path=output_path, signature_id_list=ids
            )
            cfg.ui_utils.remove_progress_bar(sound=False)
            cfg.mx.msg_inf_4()
        else:
            ids = cfg.scp_training.get_highlighted_ids(select_all=True)
            if len(ids) > 0:
                cfg.ui_utils.add_progress_bar()
                cfg.scp_training.save_signature_catalog(
                    path=output_path, signature_id_list=ids
                )
                cfg.ui_utils.remove_progress_bar(sound=False)
                cfg.mx.msg_inf_4()


# export signature file
def export_signature_as_csv():
    output_path = cfg.util_qt.get_existing_directory()
    if output_path is not False:
        ids = cfg.scp_training.get_highlighted_ids()
        if len(ids) > 0:
            cfg.ui_utils.add_progress_bar()
            cfg.scp_training.signature_catalog.export_signatures_as_csv(
                signature_id_list=ids, output_directory=output_path
            )
            cfg.ui_utils.remove_progress_bar(sound=False)
            cfg.mx.msg_inf_4()
        else:
            ids = cfg.scp_training.get_highlighted_ids(select_all=True)
            if len(ids) > 0:
                cfg.ui_utils.add_progress_bar()
                cfg.scp_training.signature_catalog.export_signatures_as_csv(
                    signature_id_list=ids, output_directory=output_path
                )
                cfg.ui_utils.remove_progress_bar(sound=False)
                cfg.mx.msg_inf_4()


# open a vector
# noinspection PyTypeChecker
def open_vector():
    vector = cfg.util_qt.get_open_file(
        None, QApplication.translate('semiautomaticclassificationplugin',
                                     'Select a vector'),
        '', 'SHP file (*.shp);;GPKG file (*.gpkg)'
    )
    if len(vector) > 0:
        cfg.dialog.ui.select_shapefile_label.setText(vector)
        fields = cfg.util_gdal.vector_fields(vector)
        cfg.dialog.ui.MC_ID_combo.clear()
        cfg.dialog.ui.MC_ID_combo.addItems(fields)
        cfg.dialog.ui.MC_Info_combo.clear()
        cfg.dialog.ui.MC_Info_combo.addItems(fields)
        cfg.dialog.ui.C_ID_combo.clear()
        cfg.dialog.ui.C_ID_combo.addItems(fields)
        cfg.dialog.ui.C_Info_combo.clear()
        cfg.dialog.ui.C_Info_combo.addItems(fields)
    else:
        cfg.dialog.ui.select_shapefile_label.setText('')
        cfg.dialog.ui.MC_ID_combo.clear()
        cfg.dialog.ui.MC_Info_combo.clear()
        cfg.dialog.ui.C_ID_combo.clear()
        cfg.dialog.ui.C_Info_combo.clear()


# import vector file from selected path in cfg.dialog.ui.select_shapefile_label
def import_vector():
    if len(cfg.dialog.ui.select_shapefile_label.text()) > 0:
        macroclass_field = cfg.dialog.ui.MC_ID_combo.currentText()
        macroclass_name_field = cfg.dialog.ui.MC_Info_combo.currentText()
        class_field = cfg.dialog.ui.C_ID_combo.currentText()
        class_name_field = cfg.dialog.ui.C_Info_combo.currentText()
        if cfg.dialog.ui.signature_checkBox_2.isChecked() is True:
            calculate_signature = True
        else:
            calculate_signature = False
        if cfg.scp_training is None:
            cfg.mx.msg_war_5()
        else:
            cfg.ui_utils.add_progress_bar()
            cfg.scp_training.save_temporary_signature_catalog()
            signature_catalog = cfg.scp_training.signature_catalog_copy()
            cfg.scp_training.set_signature_catalog(
                signature_catalog=signature_catalog
            )
            cfg.scp_training.import_vector(
                file_path=cfg.dialog.ui.select_shapefile_label.text(),
                macroclass_field=macroclass_field,
                macroclass_name_field=macroclass_name_field,
                class_field=class_field, class_name_field=class_name_field,
                calculate_signature=calculate_signature
            )
            cfg.dock_class_simpl_dlg.ui.undo_save_Button.setEnabled(True)
            cfg.dock_class_simpl_dlg.ui.redo_save_Button.setEnabled(False)
            cfg.ui_utils.remove_progress_bar(sound=False)


""" Plot """


# add signatures to spectral plot
def add_signature_to_spectral_plot(tab_index=0):
    if cfg.scp_training is not None:
        ids = cfg.scp_training.get_highlighted_ids(
            select_all=False, signatures=True
        )
        if len(ids) > 0:
            plot_catalog = cfg.spectral_signature_plotter.plot_catalog
            signature_catalog = cfg.scp_training.signature_catalog
            cfg.ui_utils.add_progress_bar()
            for _id in ids:
                if cfg.rs.configurations.action:
                    signature_catalog.export_signature_values_for_plot(
                        signature_id=_id, plot_catalog=plot_catalog
                    )
            cfg.ui_utils.remove_progress_bar(sound=False)
            cfg.spectral_signature_plotter.signature_list_plot_table()
            cfg.input_interface.spectral_plot_tab()
            cfg.input_interface.select_spectral_plot_settings_tab(tab_index)
        else:
            cfg.input_interface.spectral_plot_tab()
            cfg.input_interface.select_spectral_plot_settings_tab(tab_index)




# export symbology
def export_symbology(macroclass=True):
    if macroclass:
        value_color_dictionary = (
            cfg.scp_training.signature_catalog.macroclasses_color_string
        )
        value_name_dictionary = (
            cfg.scp_training.signature_catalog.macroclasses
        )
    else:
        classes = cfg.scp_training.signature_catalog.table.class_id.tolist()
        names = cfg.scp_training.signature_catalog.table.class_name.tolist()
        colors = cfg.scp_training.signature_catalog.table.color.tolist()
        value_name_dictionary = {}
        value_color_dictionary = {}
        for class_i in range(len(classes)):
            value_name_dictionary[classes[class_i]] = names[class_i]
            value_color_dictionary[classes[class_i]] = colors[class_i]
    return value_name_dictionary, value_color_dictionary
