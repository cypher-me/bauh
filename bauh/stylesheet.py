import os
import re
import traceback
from typing import Optional

from PyQt5.QtWidgets import QApplication

from bauh.view.util import resource

RE_WIDTH_PERCENT = re.compile(r'[\d\\.]+%w')
RE_HEIGHT_PERCENT = re.compile(r'[\d\\.]+%h')


def process_stylesheet(file_path: str) -> Optional[str]:
    with open(file_path) as f:
        stylesheet_str = f.read()

    if stylesheet_str:
        var_map = _read_var_file(file_path)
        var_map['root_img_path'] = resource.get_path('img')

        if var_map:
            for var, value in var_map.items():
                stylesheet_str = stylesheet_str.replace('@' + var, value)

        screen_size = QApplication.primaryScreen().size()
        stylesheet_str = process_width_percent_measures(stylesheet_str, screen_size.width())
        stylesheet_str = process_height_percent_measures(stylesheet_str, screen_size.height())

        return stylesheet_str


def process_width_percent_measures(stylesheet, screen_width: int) -> str:
    width_measures = RE_WIDTH_PERCENT.findall(stylesheet)

    final_sheet = stylesheet
    if width_measures:
        for m in width_measures:
            try:
                percent = float(m.split('%')[0])
                final_sheet = final_sheet.replace(m, '{}px'.format(round(screen_width * percent)))
            except ValueError:
                traceback.print_exc()

    return final_sheet


def process_height_percent_measures(stylesheet, screen_height: int) -> str:
    width_measures = RE_HEIGHT_PERCENT.findall(stylesheet)

    final_sheet = stylesheet
    if width_measures:
        for m in width_measures:
            try:
                percent = float(m.split('%')[0])
                final_sheet = final_sheet.replace(m, '{}px'.format(round(screen_height * percent)))
            except ValueError:
                traceback.print_exc()

    return final_sheet


def _read_var_file(stylesheet_file: str) -> dict:
    vars_file = stylesheet_file.replace('.qss', '.vars')
    var_map = {}

    if os.path.isfile(vars_file):
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
