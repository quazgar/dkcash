"""The window handling of dkcash happens in this module.

It contains the following classes:
- MainWindow
"""

from PyQt5 import QtGui, QtWidgets

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
        self._init_ui()
        self.show()

    def _init_ui(self):
        self.setWindowTitle("DKCash - Direktkreditverwaltung")
