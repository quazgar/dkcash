
import argparse

# import IPython; IPython.embed()
from dkcash.gui import mainapp


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

def main():
    print("main")
    parser = _create_parser()
    args = parser.parse_args()

    return mainapp.start(filename=args.gnucash_file)
