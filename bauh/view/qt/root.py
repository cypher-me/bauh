import os
import traceback
from typing import Tuple, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QLineEdit, QApplication, QDialog, QPushButton, QVBoxLayout, \
    QSizePolicy, QToolBar, QLabel

from bauh.api.abstract.context import ApplicationContext
from bauh.commons.system import new_subprocess
from bauh.view.core.config import read_config
from bauh.view.qt.components import QtComponentsManager, new_spacer
from bauh.view.util import util
from bauh.view.util.translation import I18n

ACTION_ASK_ROOT = 99


class RootDialog(QDialog):

    def __init__(self, i18n: I18n, first_try: bool = True, tries_ended: bool = False):
        super(RootDialog, self).__init__(flags=Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.i18n = i18n
        self.tries_ended = tries_ended
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.setWindowIcon(util.get_default_icon()[1])
        self.setWindowTitle(i18n['popup.root.title'])
        self.setLayout(QVBoxLayout())

        self.label_msg = QLabel(i18n['popup.root.msg'])
        self.label_msg.setObjectName('message')
        self.layout().addWidget(self.label_msg)

        self.input_password = QLineEdit()
        self.input_password.setObjectName('password')
        self.layout().addWidget(self.input_password)

        self.label_error = QLabel()
        self.label_error.setObjectName('error')
        self.layout().addWidget(self.label_error)

        if first_try:
            self.label_error.hide()
        elif tries_ended:
            self.label_error.setText(self.i18n['popup.root.bad_password.last_try'])
        else:
            self.label_error.setText(self.i18n['popup.root.bad_password.body'])

        self.lower_bar = QToolBar()
        self.layout().addWidget(self.lower_bar)

        self.lower_bar.addWidget(new_spacer())
        self.bt_ok = QPushButton(i18n['popup.root.continue'])

        if tries_ended:
            self.bt_ok.setEnabled(False)

        self.bt_ok.setCursor(QCursor(Qt.PointingHandCursor))
        self.bt_ok.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.bt_ok.setObjectName('bt_ok')
        self.bt_ok.clicked.connect(self._validate_password)
        self.bt_ok.setDefault(True)
        self.bt_ok.setAutoDefault(True)
        self.lower_bar.addWidget(self.bt_ok)

        self.bt_cancel = QPushButton()

        if tries_ended:
            self.bt_cancel.setText(self.i18n['close'].capitalize())
        else:
            self.bt_cancel.setText(i18n['popup.button.cancel'])

        self.bt_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self.bt_cancel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.bt_cancel.setObjectName('bt_cancel')
        self.bt_cancel.clicked.connect(self.close)
        self.lower_bar.addWidget(self.bt_cancel)
        self.lower_bar.addWidget(new_spacer())

        self.valid = False
        self.password = None

    def _validate_password(self):
        self.password = self.input_password.text()

        if self.label_error.isVisible():
            self.label_error.hide()

        self.bt_ok.setEnabled(False)
        self.bt_cancel.setEnabled(False)
        self.input_password.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        try:
            self.valid = validate_password(self.password)
        except:
            traceback.print_exc()
            self.valid = False

        QApplication.restoreOverrideCursor()

    @staticmethod
    def ask_password(context: ApplicationContext, i18n: I18n, app_config: Optional[dict] = None,
                     comp_manager: Optional[QtComponentsManager] = None, tries: int = 3) -> Tuple[str, bool]:

        current_config = read_config() if not app_config else app_config

        store_password = bool(current_config['store_root_password'])

        if store_password and context.root_password and validate_password(context.root_password):
            return context.root_password, True

        if comp_manager:
            comp_manager.save_states(state_id=ACTION_ASK_ROOT, only_visible=True)
            comp_manager.disable_visible()

        password = None

        try:
            for attempt in range(0, tries):
                diag = RootDialog(i18n=i18n, first_try=attempt == 0)
                diag.exec()
                password = diag.password

                if password is None:
                    break
                elif diag.valid:
                    password = diag.password
                else:
                    password = None

            if password is None:
                diag = RootDialog(i18n=i18n, first_try=False, tries_ended=True)
                diag.exec()
        except:
            if comp_manager:
                comp_manager.restore_state(ACTION_ASK_ROOT)

            traceback.print_exc()

        if password is not None and store_password:
            context.root_password = password

        return password, password is not None


def is_root():
    return os.getuid() == 0


def ask_root_password(context: ApplicationContext, i18n: I18n,
                      app_config: dict = None,
                      comp_manager: QtComponentsManager = None) -> Tuple[str, bool]:
    return RootDialog.ask_password(context=context,
                                   i18n=i18n,
                                   app_config=app_config,
                                   comp_manager=comp_manager)

    # store_password = bool(cur_config['store_root_password'])
    #
    # if store_password and context.root_password and validate_password(context.root_password):
    #     return context.root_password, True
    #
    # diag = RootDialog(i18n)
    #
    # if comp_manager:
    #     comp_manager.save_states(state_id=ACTION_ASK_ROOT, only_visible=True)
    #     comp_manager.disable_visible()
    #
    # for attempt in range(3):
    #
    #     ok = diag.show()
    #
    #     if ok:
    #         QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    #         valid = validate_password(diag.textValue())
    #         QApplication.restoreOverrideCursor()
    #
    #         if not valid:
    #             body = i18n['popup.root.bad_password.body']
    #
    #             if attempt == 2:
    #                 body += '. ' + i18n['popup.root.bad_password.last_try']
    #
    #             show_message(title=i18n['popup.root.bad_password.title'],
    #                          body=body,
    #                          type_=MessageType.ERROR)
    #             ok = False
    #             diag.setTextValue('')
    #
    #         if ok:
    #             if store_password:
    #                 context.root_password = diag.textValue()
    #
    #             if comp_manager:
    #                 comp_manager.restore_state(ACTION_ASK_ROOT)
    #
    #             return diag.textValue(), ok
    #     else:
    #         break
    #
    # if comp_manager:
    #     comp_manager.restore_state(ACTION_ASK_ROOT)
    #
    # return '', False


def validate_password(password: str) -> bool:
    clean = new_subprocess(['sudo', '-k']).stdout
    echo = new_subprocess(['echo', password], stdin=clean).stdout

    validate = new_subprocess(['sudo', '-S', '-v'], stdin=echo)

    for o in validate.stdout:
        pass

    for o in validate.stderr:
        if o:
            line = o.decode()

            if 'incorrect password attempt' in line:
                return False

    return True
