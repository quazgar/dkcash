"""The window handling of dkcash happens in this module.

It contains the following classes:
- MainWindow
"""

import os

from PyQt5 import QtGui, QtWidgets

from . import dk_widgets
from .. import db

class MainWindow(QtWidgets.QMainWindow):
    """The application's main window.

    The window consists of the following elements:
    - A menu with (all?) actions that could be done.
    - A big widget in one of several modes, with an overview or detailed view
      of:
      - The creditors
      - The accounts / contracts (overview)
      - Each account with the relevant transactions
    """
    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        self._init_db(filename)
        self._init_ui()
        self.show()

    def _init_db(self, filename):
        if (os.path.exists(filename)
            and os.stat(filename).st_size == 0):
            os.remove(filename)
        self._db = db.DKDatabase(filename)

    def _init_ui(self):
        # global settings
        self.setWindowTitle("DKCash - Direktkreditverwaltung")

        # create contained widgets
        self.creditors_w = dk_widgets.CreditorsOverview()
        self.creditor_w = None
        self.creditor_contracts_w = None
        self.all_contracts_w = None
        self.contract_detail_w = None
        self.transaction_detail_w = None

        # connect signals and slots
        self._connect_everything()

    def _connect_everything(self):
        pass

