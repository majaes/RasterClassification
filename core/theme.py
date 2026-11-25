# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Modern look of the buttons of the panel: flat, rounded and neutral (grey
shades on hover, press and check). The colors come from the palette of QGIS, so
the look follows its light or dark theme. """

from qgis.PyQt.QtWidgets import QPushButton, QToolButton

STYLE = """
QPushButton, QToolButton {
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px 10px;
    background-color: palette(button);
}
QPushButton:hover, QToolButton:hover {
    border-color: palette(dark);
    background-color: rgba(128, 128, 128, 40);
}
QPushButton:pressed, QToolButton:pressed {
    background-color: rgba(128, 128, 128, 80);
}
QPushButton:checked, QToolButton:checked {
    border-color: palette(dark);
    background-color: rgba(128, 128, 128, 80);
}
QPushButton:disabled, QToolButton:disabled {
    color: palette(mid);
    background-color: transparent;
}
QToolButton#collapsibleHeader {
    border: none;
    background-color: transparent;
    padding: 3px 2px;
}
QToolButton#collapsibleHeader:hover {
    background-color: transparent;
    border: none;
}
"""


def apply(widget):
    """ Apply the style to a widget and to its buttons (the old style of each
    button, set in the generated interface, is cleared). """
    for button in widget.findChildren((QPushButton, QToolButton)):
        if button.objectName() != 'collapsibleHeader':
            button.setStyleSheet('')
    widget.setStyleSheet(STYLE)
