# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Progress bars of the plugin panel.

One bar is placed under the Wavelength menu (band set tab) and one under the
Algorithm row (classification tab). They show the progress of the processing
and a moving bar while data are imported, with a Cancel button, and hide
themselves when finished.
"""

from qgis.PyQt.QtCore import QTimer, QObject, QEvent

from .language import tr
from qgis.PyQt.QtWidgets import (
    QProgressBar, QSizePolicy, QWidget, QHBoxLayout, QPushButton,
    QToolButton, QComboBox, QLineEdit, QAbstractSpinBox, QCheckBox,
    QRadioButton, QTabBar
)

# the progress boxes of the panel (progress bar and Cancel button)
BOXES = []
# counter used to ignore a delayed hide when a new task has started
_generation = [0]
# action called by the Cancel button (for the processing)
_cancel_callback = [None]
# True when the user has clicked Cancel
cancel_requested = [False]
# widgets locked while a processing runs (for example the satellite list)
LOCKED = []
# True while a processing or a loading runs
_active = [False]


def is_active():
    return _active[0]


def create_bar(parent):
    """ Create a hidden box with a progress bar and a Cancel button. """
    box = QWidget(parent)
    layout = QHBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    bar = QProgressBar(box)
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setTextVisible(True)
    bar.setFormat('%p%')
    bar.setMaximumHeight(18)
    bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    button = QPushButton(tr('Cancel'), box)
    button.setToolTip(tr('Cancel the processing or the loading'))
    button.clicked.connect(cancel)
    layout.addWidget(bar, 1)
    layout.addWidget(button, 0)
    box.bar = bar
    box.button = button
    # always visible: idle at 0 %, with Cancel greyed out
    button.setEnabled(False)
    box.setVisible(True)
    BOXES.append(box)
    return box


def retranslate():
    """ Texts of the buttons in the language of the plugin. """
    def set_text(box):
        box.button.setText(tr('Cancel'))
        box.button.setToolTip(tr('Cancel the processing or the loading'))
    _each(set_text)


def _each(function):
    for box in list(BOXES):
        try:
            function(box)
        except RuntimeError:
            # the widget has been deleted
            BOXES.remove(box)


def cancel():
    """ Cancel button: stop the processing or the loading. """
    cancel_requested[0] = True
    _each(lambda box: box.button.setEnabled(False))
    callback = _cancel_callback[0]
    if callback is not None:
        try:
            callback()
        except Exception as err:
            str(err)


def is_cancelled():
    return cancel_requested[0]


# tab widgets of the panel: all their options are locked while a processing
# runs, the navigation (tabs, scrolling, folding the sections) stays possible
PANELS = []
_CONTROLS = (QPushButton, QToolButton, QComboBox, QLineEdit, QAbstractSpinBox,
             QCheckBox, QRadioButton)
_BLOCKED = (
    QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
    QEvent.Type.MouseButtonDblClick, QEvent.Type.KeyPress,
    QEvent.Type.KeyRelease, QEvent.Type.Wheel
)


class _Blocker(QObject):
    """ Swallows the clicks, the keys and the wheel on the locked options; the
    enabled state of the widgets is not changed. """

    def eventFilter(self, obj, event):
        return bool(_active[0] and event.type() in _BLOCKED)


_blocker = _Blocker()
_filtered = []


def _controls():
    protected = set()
    for box in list(BOXES):
        try:
            protected.update(box.findChildren(QWidget))
            protected.add(box)
        except RuntimeError:
            BOXES.remove(box)
    found = []
    for panel in list(PANELS):
        try:
            widgets = panel.findChildren(QWidget)
        except RuntimeError:
            PANELS.remove(panel)
            continue
        for widget in widgets:
            if not isinstance(widget, _CONTROLS) or widget in protected:
                continue
            if widget.objectName() == 'collapsibleHeader':
                continue
            if isinstance(widget.parent(), QTabBar):
                continue
            found.append(widget)
    return found


def _lock_panel(state):
    for widget in _controls():
        try:
            if state and widget not in _filtered:
                widget.installEventFilter(_blocker)
                _filtered.append(widget)
            widget.setProperty('locked', bool(state))
            style = widget.style()
            style.unpolish(widget)
            style.polish(widget)
            widget.update()
        except RuntimeError:
            pass


def _lock_listed(state):
    for widget in list(LOCKED):
        try:
            widget.setEnabled(state)
        except RuntimeError:
            # the widget has been deleted
            LOCKED.remove(widget)


def _begin(callback):
    _lock_listed(False)
    _lock_panel(True)
    _generation[0] += 1
    _active[0] = True
    cancel_requested[0] = False
    _cancel_callback[0] = callback
    _each(lambda box: box.button.setEnabled(True))


def start(callback=None):
    """ Show the bars at 0 %; callback is called by the Cancel button. """
    _begin(callback)

    def show(box):
        box.bar.setRange(0, 100)
        box.bar.setValue(0)
        box.bar.setFormat('%p%')
        box.setVisible(True)
    _each(show)


def busy(text='Loading ...', callback=None):
    """ Show a moving bar (the duration is not known). """
    _begin(callback)

    def show(box):
        box.bar.setRange(0, 0)
        box.bar.setFormat(text)
        box.setVisible(True)
    _each(show)


def update(value):
    """ Set the progress, from 0 to 100. """
    try:
        value = max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return

    def set_value(box):
        if box.bar.maximum() == 0:
            box.bar.setRange(0, 100)
            box.bar.setFormat('%p%')
        if not box.isVisible():
            box.setVisible(True)
        box.bar.setValue(value)
    _each(set_value)


def _idle(box):
    box.bar.setRange(0, 100)
    box.bar.setFormat('%p%')
    box.bar.setValue(0)
    box.button.setEnabled(False)
    box.setVisible(True)


def finish():
    """ Complete the bars and hide them after a short delay. """
    _generation[0] += 1
    current = _generation[0]
    _cancel_callback[0] = None
    _active[0] = False
    _lock_listed(True)
    _lock_panel(False)

    def complete(box):
        if box.bar.maximum() == 0:
            box.bar.setRange(0, 100)
        box.bar.setFormat('%p%')
        box.bar.setValue(100)
        box.button.setEnabled(False)
    _each(complete)

    def hide():
        # do nothing if another task has started in the meantime
        if current == _generation[0]:
            _each(_idle)
    QTimer.singleShot(1200, hide)
