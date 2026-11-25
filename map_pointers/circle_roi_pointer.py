# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Map tool to draw a circular ROI: the left click sets the center, the
cursor moves to set the radius, the right click closes the circle. """

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.gui import QgsMapTool

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])


# noinspection PyArgumentList,PyPep8Naming
class CircleROIPointer(QgsMapTool):
    rightClicked = pyqtSignal(['QgsPointXY'])
    leftClicked = pyqtSignal(['QgsPointXY'])
    moved = pyqtSignal(['QgsPointXY'])

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

    def canvasMoveEvent(self, event):
        self.moved.emit(
            self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        )

    def canvasReleaseEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(
            event.pos()
        )
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit(point)
        else:
            self.leftClicked.emit(point)

    def keyPressEvent(self, event):
        # Escape cancels the circle
        if event.key() == Qt.Key.Key_Escape:
            cfg.scp_dock.cancel_circle_roi()
