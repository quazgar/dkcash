
import argparse

from IPython import embed
from dkcash.gui import mainapp


def _create_parser():
    parser = argparse.ArgumentParser(
        description='Dieses Programm verwaltet Direktkredite.')
    parser.add_argument(
        'gnucash_file', nargs="?",
        type=argparse.FileType(mode="a"),
        default=None,
        help='Dateiname der Gnucash-Datei zur Direktkredit-Verwaltung.',
    )
    return parser

def main():
    parser = _create_parser()
    args = parser.parse_args()

    filename=args.gnucash_file
    if not filename is None:
        filename.close()
        filename = filename.name

    return mainapp.start(filename)
