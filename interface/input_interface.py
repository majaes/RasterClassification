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


""" Functions of the interface used by the panel: opening the windows that
the buttons of the panel need. """

from qgis.PyQt.QtGui import QIcon, QAction

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])


# add item to menu
def add_menu_item(menu, function, icon_name, name):
    try:
        action = QAction(
            QIcon(f'{cfg.plugin_dir}/ui/icons/{icon_name}'), name,
            cfg.iface.mainWindow()
        )
    except Exception as err:
        str(err)
        action = QAction(name, cfg.iface.mainWindow())
    action.setObjectName('action')
    # noinspection PyUnresolvedReferences
    action.triggered.connect(function)
    menu.addAction(action)
    return action


# show the main window on a tab
def _show_main_tab(second_tab):
    cfg.dialog.ui.SCP_tabs.setCurrentWidget(cfg.dialog.ui.tab_basic_tools)
    cfg.dialog.ui.tabWidget_5.setCurrentWidget(second_tab)
    cfg.dialog.close()
    cfg.dialog.show()


# the download is the third tab of the panel
def select_download_products_tab():
    page = cfg.download_dock_page
    if page is not None:
        cfg.dock_class_simpl_dlg.show()
        cfg.dock_class_simpl_dlg.ui.bandset_roi_tabs.setCurrentWidget(page)


# import library signatures tab
def import_signatures_tab():
    _show_main_tab(cfg.dialog.ui.tab_Import)


# export library signatures tab
def export_signatures_tab():
    _show_main_tab(cfg.dialog.ui.tab_export)


# spectral signature plot
def spectral_plot_tab():
    cfg.spectral_plot_dlg.close()
    cfg.spectral_plot_dlg.show()


# select tab in signature plot tab
def select_spectral_plot_settings_tab(second_tab=None):
    if second_tab is not None:
        cfg.spectral_plot_dlg.ui.tabWidget.setCurrentIndex(second_tab)


# rgb changed
def rgb_combo_changed():
    cfg.utils.set_rgb_color_composite(cfg.rgb_combo.currentText())


# add classification algorithm list to combo
def add_algorithm_to_combo(algorithm_list):
    for i in algorithm_list:
        cfg.dock_class_simpl_dlg.ui.alg_combo.addItem(i)
