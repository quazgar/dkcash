import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "dkcash",
    version = "0.0.1dev",
    author = "quazgar",
    author_email = "quazgar@posteo.de",
    description = ("Direktkreditverwaltung mit GnuCash-Backend."),
    license = "GPLv3+",
    keywords = "Direktkreditverwaltung GnuCash MHS",
    # url = "http://packages.python.org/an_example_pypi_project",
    # packages=['dkcash'], #, 'tests'],
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'dkcash = dkcash.command_line:main',
        ],
    },
    long_description=read('readme.md'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
)


