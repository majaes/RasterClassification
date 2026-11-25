# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Download tab of the panel, reorganised in the order of the work: source
and search, list of the products, bands and download. The widgets are those
of the original page (the search and download code keeps working); they are
only placed in new groups. The login page goes to the Settings tab. """

from qgis.PyQt.QtCore import Qt
from .collapsible import CollapsibleBox
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QScrollArea,
    QFrame, QSizePolicy
)


def _remove(layout, widget):
    layout.removeWidget(widget)
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is not None and item.layout() is not None:
            _remove(item.layout(), widget)


def _detach(widget):
    """ Remove a widget from the layout that holds it. """
    parent = widget.parentWidget()
    while parent is not None:
        if parent.layout() is not None:
            _remove(parent.layout(), widget)
        parent = parent.parentWidget()
        if parent is not None and isinstance(parent, QScrollArea):
            break


def wrap_texts(widgets, width=30):
    """ Check boxes cannot wrap their text: line breaks are inserted. """
    import textwrap
    for widget in widgets:
        text = ' '.join(widget.text().split())
        widget.setText(textwrap.fill(text, width))


def build(ui):
    """ Build the new page from the widgets of the main window ui; return
    (scroll area, list of group boxes with their title text). """
    names_search = (
        'label_114', 'landsat_satellite_combo', 'label_107', 'UX_lineEdit_3',
        'UY_lineEdit_3', 'selectUL_toolButton_3', 'label_105', 'LX_lineEdit_3',
        'LY_lineEdit_3', 'show_area_radioButton_2', 'label_111',
        'dateEdit_from', 'label_112', 'dateEdit_to', 'label_110',
        'cloud_cover_spinBox', 'label_194', 'result_number_spinBox_2',
        'label_113', 'imageID_lineEdit', 'label_35', 'find_images_toolButton',
        'toolButton_OSM', 'label_205', 'label_206',
        'products_filter_lineEdit', 'download_images_tableWidget',
        'toolButton_display', 'remove_image_toolButton',
        'clear_table_toolButton', 'import_table_pushButton',
        'export_table_pushButton', 'image_preview_label', 'label_3',
        'check_toolButton_2', 'ancillary_data_checkBox',
        'download_if_preview_in_legend_checkBox', 'preprocess_checkBox',
        'load_in_QGIS_checkBox', 'virtual_download_checkBox',
        'create_bandset_checkBox_2', 'export_links_Button',
        'download_images_Button'
    ) + tuple(
        'checkBoxs_band_%s' % b for b in (
            '1', '2', '3', '4', '5', '6', '7', '8', '8A', '9', '10', '11',
            '12')
    )
    widgets = {n: getattr(ui, n) for n in names_search}
    for widget in widgets.values():
        _detach(widget)
    # the old titles and containers are not used any more
    for name in ('label_103', 'label_100', 'label_258'):
        getattr(ui, name).setVisible(False)
    ui.tabWidget_3.setVisible(False)
    w = widgets

    page = QWidget()
    root = QVBoxLayout(page)
    root.setSpacing(8)
    root.setContentsMargins(4, 4, 4, 4)

    # ---- 1. source and search area
    box_search = CollapsibleBox(parent=page)
    grid = QGridLayout(box_search.body)
    grid.setHorizontalSpacing(6)
    grid.addWidget(w['label_114'], 0, 0)
    grid.addWidget(w['landsat_satellite_combo'], 0, 1, 1, 3)
    grid.addWidget(w['label_107'], 1, 0)
    grid.addWidget(w['UX_lineEdit_3'], 1, 1)
    grid.addWidget(w['UY_lineEdit_3'], 1, 2)
    grid.addWidget(w['selectUL_toolButton_3'], 1, 3)
    grid.addWidget(w['label_105'], 2, 0)
    grid.addWidget(w['LX_lineEdit_3'], 2, 1)
    grid.addWidget(w['LY_lineEdit_3'], 2, 2)
    grid.addWidget(w['show_area_radioButton_2'], 2, 3)
    grid.addWidget(w['label_111'], 3, 0)
    grid.addWidget(w['dateEdit_from'], 3, 1)
    grid.addWidget(w['label_112'], 3, 2, alignment=Qt.AlignmentFlag.AlignRight)
    grid.addWidget(w['dateEdit_to'], 3, 3)
    grid.addWidget(w['label_110'], 4, 0)
    grid.addWidget(w['cloud_cover_spinBox'], 4, 1)
    grid.addWidget(w['label_194'], 4, 2, alignment=Qt.AlignmentFlag.AlignRight)
    grid.addWidget(w['result_number_spinBox_2'], 4, 3)
    grid.addWidget(w['label_113'], 5, 0)
    grid.addWidget(w['imageID_lineEdit'], 5, 1, 1, 2)
    find = QHBoxLayout()
    find.addWidget(w['label_35'])
    find.addWidget(w['find_images_toolButton'])
    grid.addLayout(find, 5, 3)
    for name in ('label_114', 'label_107', 'label_105', 'label_111',
                 'label_110', 'label_113', 'label_194', 'label_112',
                 'label_35'):
        w[name].setWordWrap(True)
    for column in (1, 2, 3):
        grid.setColumnStretch(column, 1)
    for name in ('dateEdit_from', 'dateEdit_to', 'cloud_cover_spinBox',
                 'result_number_spinBox_2', 'UX_lineEdit_3', 'UY_lineEdit_3',
                 'LX_lineEdit_3', 'LY_lineEdit_3', 'imageID_lineEdit',
                 'landsat_satellite_combo'):
        w[name].setMinimumWidth(40)
        w[name].setSizePolicy(QSizePolicy.Policy.Ignored,
                              QSizePolicy.Policy.Fixed)
    # the OpenStreetMap button and its attribution are not part of the panel
    for name in ('toolButton_OSM', 'label_205', 'label_206'):
        w[name].setVisible(False)
    root.addWidget(box_search)

    # ---- 2. products found
    box_results = CollapsibleBox(parent=page, stretch=True)
    vbox = QVBoxLayout(box_results.body)
    vbox.addWidget(w['products_filter_lineEdit'])
    w['download_images_tableWidget'].setMinimumHeight(170)
    vbox.addWidget(w['download_images_tableWidget'], 1)
    tools = QHBoxLayout()
    w['image_preview_label'].setMinimumSize(0, 0)
    w['image_preview_label'].setFixedSize(84, 84)
    tools.addWidget(w['image_preview_label'])
    for name in ('toolButton_display', 'remove_image_toolButton',
                 'clear_table_toolButton', 'import_table_pushButton',
                 'export_table_pushButton'):
        tools.addWidget(w[name])
    tools.addStretch(1)
    vbox.addLayout(tools)
    root.addWidget(box_results, 1)

    # ---- 3. bands and download
    box_download = CollapsibleBox(parent=page)
    grid_d = QGridLayout(box_download.body)
    grid_d.addWidget(w['label_3'], 0, 0, 1, 4)
    bands = ('1', '2', '3', '4', '5', '6', '7', '8', '8A', '9', '10', '11',
             '12')
    for index, band in enumerate(bands):
        grid_d.addWidget(w['checkBoxs_band_%s' % band],
                         1 + index // 4, index % 4)
    grid_d.addWidget(w['ancillary_data_checkBox'], 5, 0, 1, 3)
    grid_d.addWidget(w['check_toolButton_2'], 5, 3)
    options = QGridLayout()
    wrapped = []
    for row, name in enumerate((
            'download_if_preview_in_legend_checkBox', 'preprocess_checkBox',
            'load_in_QGIS_checkBox', 'virtual_download_checkBox',
            'create_bandset_checkBox_2')):
        options.addWidget(w[name], row, 0)
        wrapped.append(w[name])
    grid_d.addLayout(options, 6, 0, 1, 4)
    buttons = QHBoxLayout()
    buttons.addStretch(1)
    buttons.addWidget(w['export_links_Button'])
    buttons.addWidget(w['download_images_Button'])
    grid_d.addLayout(buttons, 7, 0, 1, 4)
    root.addWidget(box_download)

    scroll = QScrollArea()
    # the long texts of the options are shown on several lines
    scroll.wrapped = wrapped
    wrap_texts(wrapped)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(page)
    hidden = ('toolButton_OSM', 'label_205', 'label_206')
    for name, widget in widgets.items():
        widget.setVisible(name not in hidden)
    return scroll, (box_search, box_results, box_download)
