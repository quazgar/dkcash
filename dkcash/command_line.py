
import argparse
import sys

from PyQt5 import QtGui, QtWidgets

def _create_parser():
    parser = argparse.ArgumentParser(
        description='Dieses Programm verwaltet Direktkredite.')
    parser.add_argument(
        'gnucash_file', nargs="?",
        type=argparse.FileType(mode="w"),
        default=None,
        help='Dateiname der Gnucash-Datei zur Direktkredit-Verwaltung.',
    )
    return parser

def _get_file_name():
    filedialog = QtWidgets.QFileDialog(caption="Direktkredit-Datei")
    opts = QtWidgets.QFileDialog.DontConfirmOverwrite
    file_name = QtWidgets.QFileDialog.getSaveFileName(
        caption="Direktkredit-Datei",
        filter="Sqlite-Datenbank (*.sqlite, *.sqlite3, *.gnucash)",
        options=opts,
        )
    return file_name

def main():
    print("main")
    parser = _create_parser()
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    if args.gnucash_file is None:
        gnucash_file_name = _get_file_name()
    else:
        args.gnucash_file.close()
        gnucash_file_name = args.gnucash_file.name
    print(gnucash_file_name)
