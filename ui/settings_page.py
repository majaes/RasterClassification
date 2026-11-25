# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Settings tab of the panel: language, download sources (links, accounts,
sources added by the user) and credits. """

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QButtonGroup, QScrollArea, QFrame, QSizePolicy
)
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsTask

from .collapsible import CollapsibleBox
from ..core import language
from ..core import custom_sources
from ..core.language import tr

cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])

AUTHOR_CREDIT = (
    '<b>Raster Classification</b> %s &copy; 2026 '
    '<a href="https://anbmng.com">ANABA MANGA</a>'
)
DERIVED_CREDIT = (
    'Derived from the <a href="https://github.com/semiautomaticgit/'
    'SemiAutomaticClassificationPlugin">Semi-Automatic Classification '
    'Plugin</a> by Luca Congedo (GPL v3 or later) and built on the '
    '<a href="https://github.com/fabriziopandini/remotior_sensus">Remotior '
    'Sensus</a> library.'
)
DATA_CREDIT = (
    'Search and download: <a href="https://dataspace.copernicus.eu">'
    'Copernicus Data Space Ecosystem</a>, <a href="https://planetary'
    'computer.microsoft.com">Microsoft Planetary Computer</a>, <a '
    'href="https://www.earthdata.nasa.gov">NASA Earthdata</a> (HLS) and '
    '<a href="https://earth-search.aws.element84.com/v1">Earth Search</a> '
    '(Element 84, AWS Open Data). Map data &copy; <a href="https://www.'
    'openstreetmap.org/copyright">OpenStreetMap</a> contributors.'
)
LICENSE_CREDIT = (
    'Contains modified Copernicus Sentinel data. Respect the licence of the '
    'data of each provider.'
)


class SettingsPage(QScrollArea):
    """ The page is in a scroll area: the panel can be narrow. """

    def __init__(self, version='', parent=None):
        QScrollArea.__init__(self, parent)
        self.version = version
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        self.setWidget(content)
        root = QVBoxLayout(content)
        root.setSpacing(8)
        self.on_language_changed = None
        self._build_language(root)
        self._build_sources(root)
        self._build_accounts(root)
        self._build_credits(root)
        root.addStretch(1)
        self.retranslate()
        self.refresh_sources()

    def showEvent(self, event):
        # the list of the sources is read when the tab is shown
        self.refresh_sources()
        QScrollArea.showEvent(self, event)

    # ---- language
    def _build_language(self, root):
        self.box_language = CollapsibleBox(parent=self.widget())
        layout = QHBoxLayout(self.box_language.body)
        self.label_language = QLabel()
        layout.addWidget(self.label_language, 1)
        self.group_language = QButtonGroup(self)
        self.buttons_language = {}
        for code, text in (('fr', 'Français'), ('en', 'English')):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setMinimumWidth(110)
            self.group_language.addButton(button)
            self.buttons_language[code] = button
            layout.addWidget(button)
            button.clicked.connect(
                lambda _checked, c=code: self._choose_language(c))
        self.buttons_language[language.current_language()].setChecked(True)
        root.addWidget(self.box_language)

    def _choose_language(self, code):
        language.set_language(code)
        if self.on_language_changed is not None:
            self.on_language_changed()
        else:
            self.retranslate()

    # ---- sources
    def _build_sources(self, root):
        self.box_sources = CollapsibleBox(parent=self.widget())
        layout = QVBoxLayout(self.box_sources.body)
        self.table_sources = QTableWidget(0, 3)
        self.table_sources.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_sources.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_sources.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.table_sources.verticalHeader().setVisible(False)
        self.table_sources.setMinimumHeight(170)
        header = self.table_sources.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_sources)
        row = QHBoxLayout()
        self.button_check = QPushButton()
        self.button_check.clicked.connect(self.check_links)
        self.button_remove = QPushButton()
        self.button_remove.clicked.connect(self.remove_source)
        row.addWidget(self.button_check)
        row.addWidget(self.button_remove)
        row.addStretch(1)
        layout.addLayout(row)
        # add a source
        self.box_add = CollapsibleBox(expanded=False)
        grid = QGridLayout(self.box_add.body)
        self.edit_name = QLineEdit()
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText(
            'https://earth-search.aws.element84.com/v1')
        self.edit_collection = QLineEdit()
        self.edit_collection.setPlaceholderText('sentinel-2-l2a')
        self.edit_assets = QLineEdit()
        self.edit_assets.setPlaceholderText('red, green, blue, nir')
        self.labels_add = []
        for r, edit in enumerate((self.edit_name, self.edit_url,
                                  self.edit_collection, self.edit_assets)):
            label = QLabel()
            self.labels_add.append(label)
            grid.addWidget(label, r, 0)
            grid.addWidget(edit, r, 1)
        self.button_add = QPushButton()
        self.button_add.clicked.connect(self.add_source)
        grid.addWidget(self.button_add, 4, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.setColumnStretch(1, 1)
        layout.addWidget(self.box_add)
        root.addWidget(self.box_sources)

    def _all_sources(self):
        """ [(name, address, custom or None)] """
        custom = {s['name']: s for s in custom_sources.load()}
        names = []
        try:
            names = list(cfg.rs.configurations.product_description.keys())
        except Exception as err:
            str(err)
        names = [n for n in names if n not in custom] + list(custom)
        return [(n, custom_sources.check_address(n, custom.get(n)),
                 custom.get(n)) for n in names]

    def refresh_sources(self, results=None):
        sources = self._all_sources()
        table = self.table_sources
        table.setRowCount(len(sources))
        for row, (name, address, custom) in enumerate(sources):
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, 1 if custom else 0)
            item.setToolTip(address or '')
            table.setItem(row, 0, item)
            kind = tr('Your source') if custom else tr('Built-in source')
            table.setItem(row, 1, QTableWidgetItem(kind))
            state = QTableWidgetItem('')
            if results is not None and name in results:
                ok, text = results[name]
                state.setText('%s (%s)' % (
                    tr('working') if ok else tr('unreachable'), text))
                state.setForeground(QColor('#4caf50' if ok else '#e57373'))
            table.setItem(row, 2, state)

    def check_links(self):
        sources = self._all_sources()
        addresses = {n: a for n, a, _c in sources}
        self.button_check.setEnabled(False)
        self.button_check.setText(tr('Checking ...'))

        def work(task, addresses=addresses):
            return custom_sources.check_links(addresses)

        def done(exception, result=None):
            self.button_check.setEnabled(True)
            self.retranslate()
            if result is not None:
                self.refresh_sources(result)

        task = QgsTask.fromFunction('Raster Classification: links', work,
                                    on_finished=done)
        self._task = task
        QgsApplication.taskManager().addTask(task)

    def add_source(self):
        name = self.edit_name.text().strip()[:30]
        url = self.edit_url.text().strip()
        collection = self.edit_collection.text().strip()
        assets = self.edit_assets.text().strip()
        if not (name and url and collection):
            self._message(tr('Fill the name, the address and the '
                             'collection.'), warning=True)
            return
        existing = [n for n, _a, _c in self._all_sources()]
        if name.casefold() in [n.casefold() for n in existing]:
            self._message(tr('The source "%s" already exists.') % name,
                          warning=True)
            return
        source = {'name': name, 'url': url, 'collection': collection,
                  'assets': assets}
        sources = custom_sources.load()
        sources.append(source)
        custom_sources.save(sources)
        custom_sources.register(cfg.rs.configurations, source)
        try:
            cfg.dialog.ui.landsat_satellite_combo.addItem(name)
        except Exception as err:
            str(err)
        for edit in (self.edit_name, self.edit_url, self.edit_collection,
                     self.edit_assets):
            edit.clear()
        self.refresh_sources()
        self._message(tr('The source "%s" is added: it is in the Products '
                         'list of the Download products tab.') % name)

    def remove_source(self):
        row = self.table_sources.currentRow()
        item = self.table_sources.item(row, 0) if row >= 0 else None
        if item is None or not item.data(Qt.ItemDataRole.UserRole):
            self._message(tr('Select your own source to remove it.'),
                          warning=True)
            return
        name = item.text()
        custom_sources.save(
            [s for s in custom_sources.load() if s['name'] != name])
        custom_sources.unregister(cfg.rs.configurations, name)
        combo = cfg.dialog.ui.landsat_satellite_combo
        index = combo.findText(name)
        if index >= 0:
            combo.removeItem(index)
        self.refresh_sources()
        self._message(tr('Source removed.'))

    def _message(self, text, warning=False):
        from qgis.core import Qgis
        cfg.iface.messageBar().pushMessage(
            'Raster Classification', text,
            level=Qgis.MessageLevel.Warning if warning
            else Qgis.MessageLevel.Info, duration=6)

    # ---- accounts (the login page of the download tab is moved here)
    def _build_accounts(self, root):
        self.box_accounts = CollapsibleBox(parent=self.widget())
        self.layout_accounts = QVBoxLayout(self.box_accounts.body)
        root.addWidget(self.box_accounts)

    def set_accounts_widget(self, widget):
        # the login page keeps its natural height
        widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.layout_accounts.addWidget(widget)
        self.layout_accounts.addStretch(0)
        widget.setVisible(True)

    # ---- credits
    def _build_credits(self, root):
        self.box_credits = CollapsibleBox(parent=self.widget())
        layout = QVBoxLayout(self.box_credits.body)
        self.label_credits = QLabel()
        self.label_credits.setWordWrap(True)
        self.label_credits.setOpenExternalLinks(True)
        self.label_credits.setTextFormat(Qt.TextFormat.RichText)
        self.label_credits.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.label_credits)
        root.addWidget(self.box_credits)

    # ---- texts
    def retranslate(self):
        self.box_language.setTitle(tr('Language'))
        self.label_language.setText(tr('Interface language of the plugin'))
        self.box_sources.setTitle(tr('Download sources'))
        self.table_sources.setHorizontalHeaderLabels(
            [tr('Source'), tr('Link'), tr('State')])
        self.button_check.setText(tr('Check the links'))
        self.button_remove.setText(tr('Remove the selected source'))
        self.box_add.setTitle(tr('Add a source'))
        for label, text in zip(self.labels_add, (
                'Name of the source',
                'STAC API address (URL of the catalog)', 'Collection',
                'Assets to download (comma separated)')):
            label.setText(tr(text))
        self.button_add.setText(tr('Add'))
        self.box_accounts.setTitle(tr('Accounts'))
        self.box_credits.setTitle(tr('Credits'))
        parts = [AUTHOR_CREDIT % self.version, tr(DERIVED_CREDIT),
                 tr(DATA_CREDIT), tr(LICENSE_CREDIT)]
        self.label_credits.setText('<p>' + '</p><p>'.join(parts) + '</p>')
        if self.table_sources.rowCount():
            self.refresh_sources()


def content_parent(page):
    return page.widget() if page.widget() is not None else page
