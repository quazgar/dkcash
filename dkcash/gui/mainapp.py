import os
from os import path
import sys

from PyQt5 import QtGui, QtWidgets

def _get_file_name(filename=None):
    """Returns a valid file name, or None.

    None is returned if no valid file can be found or if the user cancels the
    file choosing process.  Invalid means that the file cannot be written or
    overwritten,

    """

    # File must either (exist and be writable) or (not exist and directory be
    # writable).
    while filename is None:
        filedialog = QtWidgets.QFileDialog(caption="Direktkredit-Datei")
        opts = QtWidgets.QFileDialog.DontConfirmOverwrite
        filename = QtWidgets.QFileDialog.getSaveFileName(
            caption="Direktkredit-Datei",
            filter="Sqlite-Datenbank (*.sqlite *.sqlite3 *.gnucash)",
            options=opts,
        )[0]
        if len(filename) == 0:
            return None

        if (path.exists(filename)
            and not os.access(filename, os.W_OK)):
            QtWidgets.QMessageBox.information(
                None,
                "Dateifehler",
                "Datei kann nicht geschrieben werden.")
            filename = None
            continue
        if (not path.exists(filename)
            and not os.access(os.path.dirname(path.abspath(filename)),
                              os.W_OK)):
            QtWidgets.QMessageBox.information(
                None,
                "Dateifehler",
                "Datei kann nicht angelegt werden.")
            filename = None
            continue
    return filename

def start(filename=None):
    app = QtWidgets.QApplication(sys.argv)
    filename = _get_file_name(filename)
    if not filename:
        print("Kein Dateiname angegeben, Programm wird beendet")
        sys.exit(1)
    print(filename)
