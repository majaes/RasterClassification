# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Modern look of the buttons of the panel: flat, rounded, with an accent
color on hover, press and check. The colors come from the palette of QGIS, so
the look follows its light or dark theme. """

from qgis.PyQt.QtWidgets import QPushButton, QToolButton

ACCENT = '#3B82F6'

STYLE = """
QPushButton, QToolButton {
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px 10px;
    background-color: palette(button);
}
QPushButton:hover, QToolButton:hover {
    border-color: %(accent)s;
    background-color: rgba(59, 130, 246, 45);
}
QPushButton:pressed, QToolButton:pressed {
    background-color: rgba(59, 130, 246, 100);
}
QPushButton:checked, QToolButton:checked {
    border-color: %(accent)s;
    background-color: rgba(59, 130, 246, 120);
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
""" % {'accent': ACCENT}


def apply(widget):
    """ Apply the style to a widget and to its buttons (the old style of each
    button, set in the generated interface, is cleared). """
    for button in widget.findChildren((QPushButton, QToolButton)):
        if button.objectName() != 'collapsibleHeader':
            button.setStyleSheet('')
    widget.setStyleSheet(STYLE)
