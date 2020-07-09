import glob
import os
import sys
from typing import Tuple

from PyQt5.QtWidgets import QApplication

from bauh import __app_name__, __version__
from bauh.api.constants import STYLES_PATH
from bauh.view.util import util, translation, resource
from bauh.view.util.translation import I18n

DEFAULT_I18N_KEY = 'en'


def new_qt_application(app_config: dict, quit_on_last_closed: bool = False, name: str = None) -> QApplication:
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

    stylesheet = app_config['ui']['stylesheet']
    stylesheet = stylesheet.strip().lower() if stylesheet else None

    if stylesheet:
        default_styles = {f.split('/')[-1].split('.')[0].lower(): f for f in glob.glob(resource.get_path('style/*.qss'))}

        stylesheet_file = default_styles.get(stylesheet)

        if not stylesheet_file:
            custom_styles = {f.split('/')[-1].split('.')[0].lower(): f for f in glob.glob('{}/*.qss'.format(STYLES_PATH))}
            stylesheet_file = custom_styles.get(stylesheet) if custom_styles else None

        if stylesheet_file:
            with open(stylesheet_file) as f:
                stylesheet_str = f.read()

            if stylesheet_str:
                var_map = _read_var_file(stylesheet_file)

                if var_map:
                    for var, value in var_map.items():
                        stylesheet_str = stylesheet_str.replace('@' + var, value)

            app.setStyleSheet(stylesheet_str)

    return app


def _read_var_file(stylesheet_file: str) -> dict:
    vars_file = stylesheet_file.replace('.qss', '.vars')
    if os.path.isfile(vars_file):
        var_map = {}
        with open(vars_file) as f:
            for line in f.readlines():
                if line:
                    line_strip = line.strip()
                    if line_strip:
                        var_value = line_strip.split('=')

                        if var_value and len(var_value) == 2:
                            var, value = var_value[0].strip(), var_value[1].strip()

                            if var and value:
                                var_map[var] = value

        return var_map

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
