import os
import sys
from logging import Logger
from typing import Tuple

from PyQt5.QtWidgets import QApplication

from bauh import __app_name__, __version__
from bauh.stylesheet import process_stylesheet, read_default_stylesheets, read_user_stylesheets, read_stylesheet_metada
from bauh.view.util import util, translation
from bauh.view.util.translation import I18n

DEFAULT_I18N_KEY = 'en'
PROPERTY_HARDCODED_STYLESHEET = 'hcqss'


def new_qt_application(app_config: dict, logger: Logger, quit_on_last_closed: bool = False, name: str = None) -> QApplication:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(quit_on_last_closed)  # otherwise windows opened through the tray icon kill the application when closed
    app.setApplicationName(name if name else __app_name__)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(util.get_default_icon()[1])

    if app_config['ui']['style']:
        app.setStyle(str(app_config['ui']['style']))
    else:
        if app.style().objectName().lower() not in {'fusion', 'breeze', 'oxygen'}:
            app.setStyle('Fusion')

    stylesheet_key = app_config['ui']['stylesheet'].strip() if app_config['ui']['stylesheet'] else None

    if not stylesheet_key:
        logger.warning("config: no stylesheet defined")
    else:
        available_stylesheets = {}
        default_styles = read_default_stylesheets()
        available_stylesheets.update(default_styles)

        stylesheet_file = None

        if '/' in stylesheet_key:
            if os.path.isfile(stylesheet_key):
                user_sheets = read_user_stylesheets()

                if user_sheets:
                    available_stylesheets.update(user_sheets)

                    if stylesheet_key in user_sheets:
                        stylesheet_file = stylesheet_key
        else:
            stylesheet_file = default_styles.get(stylesheet_key)

        if stylesheet_file:
            with open(stylesheet_file) as f:
                stylesheet_str = f.read()

            if not stylesheet_str:
                logger.warning("stylesheet file '{}' has no content".format(stylesheet_file))
            else:
                base_metadata = read_stylesheet_metada(key=stylesheet_key, file_path=stylesheet_file)

                if base_metadata.abstract:
                    logger.warning("stylesheet file '{}' is abstract (abstract = true) and cannot be loaded".format(stylesheet_file))
                else:
                    processed = process_stylesheet(file_path=stylesheet_file,
                                                   metadata=base_metadata,
                                                   stylesheet_str=stylesheet_str,
                                                   available_sheets=available_stylesheets)

                    if processed:
                        app.setStyleSheet(processed[0])
                        app.setProperty(PROPERTY_HARDCODED_STYLESHEET, processed[1].hardcoded_stylesheets)
                        logger.info("stylesheet file '{}' loaded".format(stylesheet_file))
                    else:
                        logger.warning("stylesheet file '{}' could not be interpreted and processed".format(stylesheet_file))

    if not app_config['ui']['system_stylesheets']:
        app.setPalette(app.style().standardPalette())

    return app


def _gen_i18n_data(app_config: dict, locale_dir: str) -> Tuple[str, dict, str, dict]:
    i18n_key, current_i18n = translation.get_locale_keys(app_config['locale'], locale_dir=locale_dir)
    default_i18n = translation.get_locale_keys(DEFAULT_I18N_KEY, locale_dir=locale_dir)[1] if i18n_key != DEFAULT_I18N_KEY else {}
    return i18n_key, current_i18n, DEFAULT_I18N_KEY, default_i18n


def generate_i18n(app_config: dict, locale_dir: str) -> I18n:
    return I18n(*_gen_i18n_data(app_config, locale_dir))


def update_i18n(app_config, locale_dir: str, i18n: I18n) -> I18n:
    cur_key, cur_dict, def_key, def_dict = _gen_i18n_data(app_config, locale_dir)

    if i18n.current_key == cur_key:
        i18n.current.update(cur_dict)

    i18n.default.update(def_dict)
    return i18n
