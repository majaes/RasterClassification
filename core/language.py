# Raster Classification
# Copyright (C) 2026 ANABA MANGA (https://anbmng.com).
# Derived from the Semi-Automatic Classification Plugin by Luca Congedo
# (GPL v3 or later). This file is part of Raster Classification and is
# distributed under the same license.

""" Language of the plugin (English or French), changed from the Settings tab
without restarting QGIS.

English is the source language. French is installed as a dictionary
translator for the contexts of the plugin; the texts written by hand in the
panel go through tr(). """

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator

from .fr_translations import FR
from .fr_extra import FR_EXTRA, REPLACE_RULES

SETTING_KEY = 'RasterClassification/language'
LANGUAGES = ('en', 'fr')
# Qt contexts of the plugin (generated interfaces and hand written texts)
CONTEXTS = {
    'DockClassSimplified', 'DockClass', 'SemiAutomaticClassificationPlugin',
    'semiautomaticclassificationplugin', 'SCP_Widget', 'ScatterPlot',
    'SpectralSignaturePlot', 'RasterClassification'
}

# texts written by hand (panel, messages, Settings tab)
EXTRA = {
    'Band set definition': 'Définition du jeu de bandes',
    'ROI & Classification': 'ROI et classification',
    'ROI && Classification': 'ROI et classification',
    'Download products': 'Téléchargement',
    'Settings': 'Paramètres',
    'Training file': "Fichier d'entraînement",
    'Class': 'Classe',
    'ROI': 'ROI',
    'Name': 'Nom',
    'Create': 'Créer',
    'Delete Class': 'Supprimer la classe',
    'Delete ROI': 'Supprimer ROI',
    'Circle': 'Cercle',
    'Polygon': 'Polygone',
    'Undo': 'Annuler',
    'Redo': 'Rétablir',
    'Spectral plot': 'Graphique spectral',
    'New file': 'Nouveau fichier',
    'Open file': 'Ouvrir un fichier',
    'Import file': 'Importer un fichier',
    'Export ROIs': 'Exporter les ROI',
    'Reset': 'Réinitialiser',
    'Add layer': 'Ajouter une couche',
    'Move up': 'Monter',
    'Move down': 'Descendre',
    'Delete row': 'Supprimer la ligne',
    'Satellite': 'Satellite',
    'Composition': 'Composition',
    'Band name': 'Nom de bande',
    'Center wavelength': "Longueur d'onde centrale",
    'Traitement': 'Traitement',
    'Processing': 'Traitement',
    'Algorithm': 'Algorithme',
    'Preview': 'Aperçu',
    'RUN': 'Lancer',
    'Cancel': 'Annuler',
    'Cancel the processing or the loading':
        'Annuler le traitement ou le chargement',
    'Natural color (true color)': 'Couleurs naturelles (vraies couleurs)',
    'Color infrared (vegetation in red)':
        'Infrarouge couleur (végétation en rouge)',
    'Agriculture': 'Agriculture',
    'Healthy vegetation': 'Végétation saine',
    'Short-wave infrared': 'Infrarouge à ondes courtes',
    'Urban': 'Urbain',
    'Geology': 'Géologie',
    'NDVI - vegetation': 'NDVI - végétation',
    'NDWI - water': 'NDWI - eau',
    'NDBI - built-up': 'NDBI - zones bâties',
    'NBR - burned areas': 'NBR - zones brûlées',
    'Other (choose the bands)': 'Autre (choisir les bandes)',
    # download tab and credits
    'Search parameters': 'Paramètres de recherche',
    'Product list': 'Liste de produits',
    'Download': 'Télécharger',
    'Derived from the <a href="https://github.com/semiautomaticgit/'
    'SemiAutomaticClassificationPlugin">Semi-Automatic Classification '
    'Plugin</a> by Luca Congedo (GPL v3 or later) and built on the '
    '<a href="https://github.com/fabriziopandini/remotior_sensus">Remotior '
    'Sensus</a> library.':
        'Dérivé du <a href="https://github.com/semiautomaticgit/'
        'SemiAutomaticClassificationPlugin">Semi-Automatic Classification '
        'Plugin</a> de Luca Congedo (GPL v3 ou ultérieure) et construit sur '
        'la bibliothèque <a href="https://github.com/fabriziopandini/'
        'remotior_sensus">Remotior Sensus</a>.',
    'Search and download: <a href="https://dataspace.copernicus.eu">'
    'Copernicus Data Space Ecosystem</a>, <a href="https://planetary'
    'computer.microsoft.com">Microsoft Planetary Computer</a>, <a '
    'href="https://www.earthdata.nasa.gov">NASA Earthdata</a> (HLS) and '
    '<a href="https://earth-search.aws.element84.com/v1">Earth Search</a> '
    '(Element 84, AWS Open Data). Map data &copy; <a href="https://www.'
    'openstreetmap.org/copyright">OpenStreetMap</a> contributors.':
        'Recherche et téléchargement : <a href="https://dataspace.'
        'copernicus.eu">Copernicus Data Space Ecosystem</a>, <a '
        'href="https://planetarycomputer.microsoft.com">Microsoft Planetary '
        'Computer</a>, <a href="https://www.earthdata.nasa.gov">NASA '
        'Earthdata</a> (HLS) et <a href="https://earth-search.aws.element84.'
        'com/v1">Earth Search</a> (Element 84, AWS Open Data). Données '
        'cartographiques &copy; contributeurs <a href="https://www.'
        'openstreetmap.org/copyright">OpenStreetMap</a>.',
    'Contains modified Copernicus Sentinel data. Respect the licence of the '
    'data of each provider.':
        'Contient des données Copernicus Sentinel modifiées. Respectez la '
        'licence des données de chaque fournisseur.',
    'The class %s already exists: each class is unique.':
        'La classe %s existe déjà : chaque classe est unique.',
    '%s needs the band(s): %s. Add them to the band set.':
        '%s nécessite la ou les bandes : %s. Ajoutez-les au jeu de bandes.',
    'Unable to open band %s': 'Impossible d\'ouvrir la bande %s',
    'Calculating %s in the background (progress in the Tasks panel, you '
    'can keep working). The result is added to the map when finished.':
        'Calcul de %s en arrière-plan (progression dans le panneau des '
        'tâches, vous pouvez continuer à travailler). Le résultat est '
        'ajouté à la carte à la fin.',
    '%s calculation stopped.': 'Le calcul de %s est arrêté.',
    'Unable to open the %s result': 'Impossible d\'ouvrir le résultat %s',
    '%s calculated: %s': '%s calculé : %s',
    'Classification failed: %s': 'La classification a échoué : %s',
    'Preview failed: %s': "L'aperçu a échoué : %s",
    'Satellite detected: %s. You can change it in the Wavelength menu.':
        'Satellite détecté : %s. Vous pouvez le changer dans le menu '
        'Satellite.',
    'Loading cancelled.': 'Chargement annulé.',
    'Loading bands ...': 'Chargement des bandes ...',
    'Add bands to the band set first (Open file or Add layer).':
        "Ajoutez d'abord des bandes au jeu de bandes (Ouvrir un fichier ou "
        "Ajouter une couche).",
    'Band set': 'Jeu de bandes',
    'Satellite and composition': 'Satellite et composition',
    'Classes and ROIs': 'Classes et ROI',
    # Settings tab
    'Language': 'Langue',
    'Interface language of the plugin': "Langue de l'interface du plugin",
    'Download sources': 'Sources de téléchargement',
    'Accounts': 'Comptes',
    'Check the links': 'Vérifier les liens',
    'Checking ...': 'Vérification ...',
    'Source': 'Source',
    'Link': 'Lien',
    'State': 'État',
    'working': 'fonctionne',
    'unreachable': 'inaccessible',
    'Add a source': 'Ajouter une source',
    'Name of the source': 'Nom de la source',
    'STAC API address (URL of the catalog)':
        'Adresse de l\'API STAC (URL du catalogue)',
    'Collection': 'Collection',
    'Assets to download (comma separated)':
        'Fichiers à télécharger (séparés par des virgules)',
    'Add': 'Ajouter',
    'Remove the selected source': 'Retirer la source sélectionnée',
    'Remove': 'Retirer',
    'Credits': 'Crédits',
    'Built-in source': 'Source intégrée',
    'Your source': 'Votre source',
    'Fill the name, the address and the collection.':
        "Renseignez le nom, l'adresse et la collection.",
    'The source "%s" is added: it is in the Products list of the Download '
    'products tab.':
        'La source « %s » est ajoutée : elle est dans la liste Produits de '
        "l'onglet Téléchargement.",
    'The source "%s" already exists.': 'La source « %s » existe déjà.',
    'Source removed.': 'Source retirée.',
    'Select your own source to remove it.':
        'Sélectionnez une de vos sources pour la retirer.',
    'Language changed.': 'Langue modifiée.',
    # messages of the ROI tools and the classification
    'Polygon: left click adds a vertex, right click closes the polygon '
    'and adds it to the class.':
        "Polygone : le clic gauche ajoute un sommet, le clic droit ferme le "
        "polygone et l'ajoute à la classe.",
    'Circle: left click sets the center, move the cursor, right click '
    'sets the radius and adds the circle to the class (Esc cancels).':
        "Cercle : le clic gauche place le centre, déplacez le curseur, le "
        "clic droit fixe le rayon et ajoute le cercle à la classe (Échap "
        "annule).",
    'Enter a name for the class.': 'Saisissez un nom pour la classe.',
    'No training file yet: choose where to create it.':
        "Pas encore de fichier d'entraînement : choisissez où le créer.",
    'Create the class first: enter its number and name, then click '
    'Save. The ROI was not added.':
        "Créez d'abord la classe : saisissez son numéro et son nom, puis "
        "cliquez sur Créer. Le ROI n'a pas été ajouté.",
    'The class %s already exists: each class is unique.':
        'La classe %s existe déjà : chaque classe est unique.',
    'A class named "%s" already exists: each class is unique.':
        'Une classe nommée « %s » existe déjà : chaque classe est unique.',
    'Class %s (%s) created: draw its ROIs with Polygon or Circle, the '
    'right click adds each ROI to it. For another class, change the '
    'number and the name, then Save.':
        'Classe %s (%s) créée : dessinez ses ROI avec Polygone ou Cercle, '
        'le clic droit ajoute chaque ROI à la classe. Pour une autre '
        'classe, changez le numéro et le nom, puis Créer.',
    'Left click first to set the center of the circle.':
        "Cliquez d'abord (clic gauche) pour placer le centre du cercle.",
    'Select the class to delete in the list.':
        'Sélectionnez la classe à supprimer dans la liste.',
    'Preview: click on the map where you want to see the classification '
    '(a small area around the click is classified).':
        "Aperçu : cliquez sur la carte à l'endroit où voir la "
        "classification (une petite zone autour du clic est classée).",
    'Preview switched off.': 'Aperçu désactivé.',
    'Preview added to the map (layer at the top of the list).':
        "Aperçu ajouté à la carte (couche en haut de la liste).",
    'Classification finished: the map is added to the layers.':
        'Classification terminée : la carte est ajoutée aux couches.',
    'Wait for the running processing to finish.':
        'Attendez la fin du traitement en cours.',
    'Wait for the running processing': 'Attendre la fin du traitement',
    'Create the class (number and name) that receives the ROIs':
        'Créer la classe (numéro et nom) qui reçoit les ROI',
    'Delete the selected class with all its ROIs':
        'Supprimer la classe sélectionnée avec tous ses ROI',
    'Show or hide the Raster Classification panel':
        'Afficher ou masquer le panneau Raster Classification',
    'Circle ROI: left click = center, move, right click = radius (adds the '
    'circle to the class)':
        'ROI cercle : clic gauche = centre, déplacer, clic droit = rayon '
        '(ajoute le cercle à la classe)',
    'Polygon ROI: left click = vertex, right click = close (adds the '
    'polygon to the class)':
        'ROI polygone : clic gauche = sommet, clic droit = fermer (ajoute le '
        'polygone à la classe)',
    'Preview: click to switch on, then click on the map; click again to '
    'switch off':
        "Aperçu : cliquez pour activer, puis cliquez sur la carte ; "
        "recliquez pour désactiver",
}




_state = {'code': 'en', 'translator': None}


def current_language():
    return _state['code']


def _lookup_plain(source):
    text = EXTRA.get(source)
    if text is None:
        text = FR_EXTRA.get(source)
    if text is None:
        text = FR.get(source)
    return text


def lookup(source):
    """ French text of a source text (None when there is none). """
    if not source:
        return None
    text = _lookup_plain(source)
    if text is None and source.startswith('<html><head/><body><p>') and (
            source.endswith('</p></body></html>')):
        # tooltips of the generated interfaces
        inner = source[len('<html><head/><body><p>'):-len('</p></body></html>')]
        translated = lookup(inner)
        if translated is not None:
            text = '<html><head/><body><p>%s</p></body></html>' % translated
    if text is None and ('<' in source):
        # rich texts: parts are replaced
        changed = source
        for english, french in REPLACE_RULES:
            changed = changed.replace(english, french)
        if changed != source:
            text = changed
    if text is None:
        stripped = source.strip()
        if stripped and stripped != source:
            text = _lookup_plain(stripped)
            if text is not None:
                lead = source[:len(source) - len(source.lstrip())]
                trail = source[len(source.rstrip()):]
                text = lead + text + trail
    return text


class DictTranslator(QTranslator):
    """ Translator based on the dictionaries, for the plugin contexts. """

    def translate(self, context, source_text, disambiguation=None, n=-1):
        if context not in CONTEXTS:
            return None
        return lookup(source_text)

    def isEmpty(self):
        return False


def tr(text):
    """ Text of the hand written parts of the interface, in the language. """
    return QCoreApplication.translate('RasterClassification', text)


def set_language(code, remember=True):
    """ Switch the plugin to 'en' or 'fr'. """
    if code not in LANGUAGES:
        return
    translator = _state['translator']
    if translator is not None:
        QCoreApplication.removeTranslator(translator)
        _state['translator'] = None
    if code == 'fr':
        # a reference is kept: a translator that is collected stops working
        _state['translator'] = DictTranslator()
        QCoreApplication.installTranslator(_state['translator'])
    _state['code'] = code
    if remember:
        QSettings().setValue(SETTING_KEY, code)


def use_qm_files():
    """ True when the language follows QGIS ('auto'): the old translation
    files of the plugin are then used. """
    return str(QSettings().value(SETTING_KEY, 'en')) == 'auto'
