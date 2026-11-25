# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Section of the panel that can be folded (drop-down menu): a title with
an arrow, and a body that is shown or hidden. All the tabs use it, so they
look the same. """

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QFrame, QSizePolicy, QLabel
)

_MAX = 16777215


class CollapsibleBox(QWidget):

    def __init__(self, title='', parent=None, expanded=True, stretch=False,
                 collapsible=True):
        QWidget.__init__(self, parent)
        self._stretch = stretch
        self._collapsible = collapsible
        if not collapsible:
            # a simple title, without arrow and without folding
            self.header = QLabel(title, self)
            self.header.setStyleSheet(
                'QLabel { font-weight: bold; padding: 3px 2px; }')
            self.body = QFrame(self)
            self.body.setFrameShape(QFrame.Shape.StyledPanel)
            self.body.setFrameShadow(QFrame.Shadow.Sunken)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.header)
            layout.addWidget(self.body)
            if stretch:
                self.setSizePolicy(QSizePolicy.Policy.Preferred,
                                   QSizePolicy.Policy.Expanding)
            return
        self.header = QToolButton(self)
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setStyleSheet(
            'QToolButton { border: none; font-weight: bold; '
            'text-align: left; padding: 3px 2px; }')
        self.header.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.body = QFrame(self)
        self.body.setFrameShape(QFrame.Shape.StyledPanel)
        self.body.setFrameShadow(QFrame.Shadow.Sunken)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.body)
        self.header.toggled.connect(self._toggled)
        self._toggled(expanded)

    def _toggled(self, checked):
        self.header.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.body.setVisible(checked)
        if checked:
            self.setMaximumHeight(_MAX)
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding if self._stretch
                else QSizePolicy.Policy.Preferred)
        else:
            # folded: only the title takes room
            self.setMaximumHeight(self.header.sizeHint().height() + 2)
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def setTitle(self, text):
        self.header.setText(text)

    def title(self):
        return self.header.text()

    def setExpanded(self, expanded):
        if self._collapsible:
            self.header.setChecked(expanded)
