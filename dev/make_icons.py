"""Generate the icons of the plugin (modern, flat, neutral).

Usage (from the repository root, with the Python of QGIS for the PNG):
    python dev/make_icons.py

Each icon is a single neutral grey glyph drawn with round strokes, readable on
the light and the dark themes of QGIS. The files keep the names that the
interface already uses.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'ui', 'icons')

COLORS = {
    'blue': ('#5AA9FF', '#2563EB'),
    'green': ('#4ADE80', '#15A34A'),
    'red': ('#FB7185', '#E11D48'),
    'orange': ('#FDBA3B', '#F97316'),
    'purple': ('#B197FC', '#7C3AED'),
    'teal': ('#2DD4BF', '#0F9E8E'),
    'slate': ('#94A3B8', '#475569'),
    'pink': ('#F9A8D4', '#DB2777'),
}

S = 'fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
F = 'fill="#fff"'

GLYPHS = {
    # files
    'open_file': ('blue', '<path d="M4.5 8.5h5l2 2h8v7.5a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1z" %s/>' % S),
    'open_dir': ('blue', '<path d="M4.5 8.5h5l2 2h8v7.5a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1z" %s/><path d="M4.5 12.5h15" %s/>' % (S, S)),
    'new_file': ('blue', '<path d="M7 4.5h6.5l4 4v11H7z" %s/><path d="M12 11v6M9 14h6" %s/>' % (S, S)),
    'import': ('blue', '<path d="M12 5v9.5M8 10.5l4 4 4-4M6 18.5h12" %s/>' % S),
    'export': ('blue', '<path d="M12 14.5V5M8 9l4-4 4 4M6 18.5h12" %s/>' % S),
    'import_spectral_library': ('blue', '<path d="M12 5v9M8.5 10.5l3.5 3.5 3.5-3.5M6 18.5h12M6 5.5h3" %s/>' % S),
    'export_spectral_library': ('blue', '<path d="M12 14V5M8.5 8.5 12 5l3.5 3.5M6 18.5h12M15 5.5h3" %s/>' % S),
    # edit
    'add': ('green', '<path d="M12 6v12M6 12h12" %s/>' % S),
    'remove': ('red', '<path d="M6 12h12" %s/>' % S),
    'reset': ('red', '<path d="M18 12a6 6 0 1 1-1.8-4.3M18 5.5v4h-4" %s/>' % S),
    'reload': ('teal', '<path d="M18 12a6 6 0 1 1-1.8-4.3M18 5.5v4h-4" %s/>' % S),
    'move_up': ('teal', '<path d="M12 18V7M7 11.5 12 6.5l5 5" %s/>' % S),
    'move_down': ('teal', '<path d="M12 6v11M7 12.5l5 5 5-5" %s/>' % S),
    'select_all': ('teal', '<rect x="6" y="6" width="12" height="12" rx="2" %s/><path d="m9.5 12 2 2 3.5-4" %s/>' % (S, S)),
    'enter': ('teal', '<path d="M18 6v7H8M11.5 9.5 8 13l3.5 3.5" %s/>' % S),
    'options': ('slate', '<path d="M5 8.5h14M5 15.5h14" %s/><circle cx="9" cy="8.5" r="2" fill="#fff"/><circle cx="15" cy="15.5" r="2" fill="#fff"/>' % S),
    'help': ('slate', '<path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1 1-1.1 1.8" %s/><circle cx="12" cy="17" r="1.1" fill="#fff"/>' % S),
    'save_roi': ('green', '<path d="M6 5.5h10l3 3v10H6z" %s/><path d="M9 5.5v4h6v-4M9 18.5v-5h6v5" %s/>' % (S, S)),
    'undo_save_roi': ('slate', '<path d="M9 8 5.5 11.5 9 15M6 11.5h8a4 4 0 0 1 0 8h-2" %s/>' % S),
    'redo_save_roi': ('slate', '<path d="M15 8l3.5 3.5L15 15M18 11.5h-8a4 4 0 0 0 0 8h2" %s/>' % S),
    'undo_edit_raster': ('slate', '<path d="M9 8 5.5 11.5 9 15M6 11.5h8a4 4 0 0 1 0 8h-2" %s/>' % S),
    # ROI
    'manual_ROI': ('orange', '<path d="M6.5 16.5 5.5 8l8.5-2.5 4.5 5.5-4 6.5z" %s/><circle cx="6.5" cy="16.5" r="1.4" fill="#fff"/><circle cx="5.5" cy="8" r="1.4" fill="#fff"/><circle cx="14" cy="5.5" r="1.4" fill="#fff"/><circle cx="18.5" cy="11" r="1.4" fill="#fff"/><circle cx="14.5" cy="17.5" r="1.4" fill="#fff"/>' % S),
    'roi_single': ('orange', '<circle cx="12" cy="12" r="6.5" %s stroke-dasharray="2.6 2.4"/><circle cx="12" cy="12" r="1.6" fill="#fff"/>' % S),
    'pointer_tool': ('orange', '<path d="M7 5.5 17.5 11l-4.5 1.3L11.5 17z" %s/>' % S),
    'zoom_to_ROI': ('orange', '<circle cx="11" cy="11" r="5" %s/><path d="m15 15 4 4M11 9v4M9 11h4" %s/>' % (S, S)),
    # classification
    'preview': ('purple', '<path d="M3.5 12S6.5 6.5 12 6.5 20.5 12 20.5 12 17.5 17.5 12 17.5 3.5 12 3.5 12z" %s/><circle cx="12" cy="12" r="2.4" %s/>' % (S, S)),
    'run': ('green', '<path d="M8.5 6.5 18 12l-9.5 5.5z" %s stroke-width="1.5"/>' % F),
    'rgb_tool': ('purple', '<circle cx="9.7" cy="10" r="3.7" %s/><circle cx="14.3" cy="10" r="3.7" %s/><circle cx="12" cy="14" r="3.7" %s/>' % (S, S, S)),
    'threshold_tool': ('purple', '<path d="M5 12h14M9 8v8M15 8v8" %s/>' % S),
    'accuracy_tool': ('purple', '<circle cx="12" cy="12" r="7" %s/><circle cx="12" cy="12" r="3" %s/>' % (S, S)),
    'batch': ('purple', '<path d="m12 5 8 4-8 4-8-4zM4 13l8 4 8-4" %s/>' % S),
    'landsat8_tool': ('blue', '<circle cx="12" cy="12" r="3.2" %s/><ellipse cx="12" cy="12" rx="8" ry="3.2" transform="rotate(-35 12 12)" %s/>' % (S, S)),
    'add_bandset_tool': ('green', '<path d="m12 5 7 3.5-7 3.5-7-3.5zM5 12.5l7 3.5 3-1.5M17 15v5M14.5 17.5h5" %s/>' % S),
    # plots
    'sign_tool': ('purple', '<path d="M5.5 5.5v13h13M8 15.5l3-5 3 3 4-6" %s/>' % S),
    'add_sign_tool': ('purple', '<path d="M5.5 5.5v13h13M8 15.5l3-5 3 3 2-3M17 5v5M14.5 7.5h5" %s/>' % S),
    'merge_sign_tool': ('purple', '<path d="m6 6 6 6 6-6M12 12v7" %s/>' % S),
    'calculate_spectral_distances': ('purple', '<circle cx="7" cy="16.5" r="1.8" %s/><circle cx="17" cy="7.5" r="1.8" %s/><path d="m8.5 15 7-6" %s/>' % (S, S, S)),
    'fit_plot': ('teal', '<path d="M5.5 9.5v-4h4M18.5 9.5v-4h-4M5.5 14.5v4h4M18.5 14.5v4h-4" %s/>' % S),
    'save_plot_image': ('teal', '<rect x="5" y="6" width="14" height="12" rx="2" %s/><path d="m5.5 16 4-4 3 3 2.5-2.5L18.5 16" %s/><circle cx="15.5" cy="9.5" r="1" fill="#fff"/>' % (S, S)),
    # download
    'download_search': ('blue', '<circle cx="11" cy="11" r="5.2" %s/><path d="m15 15 4.5 4.5" %s/>' % (S, S)),
    'search_images': ('blue', '<circle cx="11" cy="11" r="5.2" %s/><path d="m15 15 4.5 4.5" %s/>' % (S, S)),
    'download_login': ('blue', '<circle cx="12" cy="9" r="3.2" %s/><path d="M6 19c0-3.2 2.7-5.2 6-5.2s6 2 6 5.2" %s/>' % (S, S)),
    'download_arrow': ('green', '<path d="M12 5v10M7.5 11l4.5 4.5 4.5-4.5M6 19h12" %s/>' % S),
    'download_image_preview': ('purple', '<rect x="5" y="6" width="14" height="12" rx="2" %s/><path d="m5.5 16 4-4 3 3 2.5-2.5L18.5 16" %s/><circle cx="15.5" cy="9.5" r="1" fill="#fff"/>' % (S, S)),
    'osm_add': ('teal', '<circle cx="12" cy="12" r="7" %s/><path d="M5 12h14M12 5c3 3 3 11 0 14M12 5c-3 3-3 11 0 14" %s/>' % (S, S)),
    'order_by_name': ('teal', '<path d="M5 7.5h6M5 12h4M5 16.5h2M17 6v12M14 15l3 3 3-3" %s/>' % S),
    'order_by_date': ('teal', '<rect x="5.5" y="7" width="13" height="12" rx="2" %s/><path d="M5.5 11h13M9 5v3M15 5v3" %s/>' % (S, S)),
    'docks': ('slate', '<rect x="5" y="6" width="14" height="12" rx="2" %s/><path d="M14 6v12" %s/>' % (S, S)),
}


NEUTRAL = '#8B929C'


def svg(name):
    glyph = GLYPHS[name][1].replace('#fff', NEUTRAL)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24">%s</svg>\n' % glyph
    )


MAIN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
    '<rect x="2" y="2" width="60" height="60" rx="14" fill="#343A46"/>'
    '<g fill="#C9CED6">'
    '<rect x="11" y="11" width="13" height="13" rx="2.5" opacity="0.95"/>'
    '<rect x="25.5" y="11" width="13" height="13" rx="2.5" opacity="0.6"/>'
    '<rect x="40" y="11" width="13" height="13" rx="2.5" opacity="0.35"/>'
    '<rect x="11" y="25.5" width="13" height="13" rx="2.5" opacity="0.6"/>'
    '<rect x="25.5" y="25.5" width="13" height="13" rx="2.5" opacity="0.95"/>'
    '<rect x="40" y="25.5" width="13" height="13" rx="2.5" opacity="0.6"/>'
    '<rect x="11" y="40" width="13" height="13" rx="2.5" opacity="0.35"/>'
    '<rect x="25.5" y="40" width="13" height="13" rx="2.5" opacity="0.6"/>'
    '<rect x="40" y="40" width="13" height="13" rx="2.5" opacity="0.95"/></g></svg>\n'
)

CURSOR = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
    '<circle cx="12" cy="12" r="7" fill="none" stroke="#fff" stroke-width="4"/>'
    '<circle cx="12" cy="12" r="7" fill="none" stroke="#111" stroke-width="2"/>'
    '<path d="M12 2v5M12 17v5M2 12h5M17 12h5" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
    '<path d="M12 2v5M12 17v5M2 12h5M17 12h5" stroke="#111" stroke-width="2" stroke-linecap="round"/></svg>\n'
)


def main():
    os.makedirs(os.path.join(OUT, 'pointer'), exist_ok=True)
    for name in GLYPHS:
        with open(os.path.join(OUT, 'raster_classification_%s.svg' % name), 'w', encoding='utf-8') as f:
            f.write(svg(name))
    with open(os.path.join(OUT, 'raster_classification.svg'), 'w', encoding='utf-8') as f:
        f.write(MAIN)
    with open(os.path.join(OUT, 'help.svg'), 'w', encoding='utf-8') as f:
        f.write(svg('help'))
    with open(os.path.join(OUT, 'pointer', 'ROI_pointer.svg'), 'w', encoding='utf-8') as f:
        f.write(CURSOR)
    # the PNG of the plugin (QGIS plugin manager and toolbar)
    try:
        from qgis.core import QgsApplication
        app = QgsApplication([], False)
        app.initQgis()
        from qgis.PyQt.QtGui import QImage, QPainter
        from qgis.PyQt.QtCore import Qt
        from qgis.PyQt.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(os.path.join(OUT, 'raster_classification.svg'))
        image = QImage(64, 64, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        image.save(os.path.join(ROOT, 'raster_classification.png'))
    except Exception as err:
        print('PNG not written:', err)
    print('%d icons' % (len(GLYPHS) + 3))


if __name__ == '__main__':
    main()
