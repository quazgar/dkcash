"""This module handles the backend database.

Use it as the connecting layer to a GnuCash database.  This module only does
"dumb" transactions, for more high-level needs, use the `dkhandle` module.

Because the same Sqlite GnuCash file is used for GnuCash specific operations
(account and transactions) and for storing loan specific information, frequent
opening and closing of the database connection on demand may be necessary.
"""

import os

import piecash

class DKData:
    def __init__(self, gnucash_file="dkcash_data.sql", base_account=None):
        """Represents the DKCash data.
        
Parameters
----------
gnucash_file : String, optional.
    File name of the GnuCash file, default value is "dkcash_data".  If the file
    does not exist yet, it is created.

base_account : String, optional
    The base account where the "special" accounts should be created if they do
    not yet exist.  This is a slash-separated string, for example
    `/Aktiva/DKVerwaltung`.
"""
        self._book = None

        self._gnucash_file = gnucash_file
        if not os.path.exists(gnucash_file):
            self._create_gnucash_file()

        self._base_account = base_account
        self._init_gnucash()
        self._init_tables()

    def _create_gnucash_file(self):
        """Creates the GnuCash file for this DKData object.

The GnuCash file must not exist yet."""
        piecash.create_book(self._gnucash_file)
        
    def _open_gnucash(self):
        """Initialize the GnuCash database with the necessary accounts.

Also initializes a number of GnuCash specific attributes, which only are valid
until the book is closed again.

`self._book` is open after this method.
        """
        if not self._book:
            self._book = piecash.open_book(self._gnucash_file)
        def self._EUR = self._book.commodities.get(mnemonic="EUR")
        parent = self._get_base_account()

    def _init_tables(self):
        """Initialize the GnuCash database with extra tables."""

    def _get_base_account(self):
        """Returns the base account for this object.

Requires an opened book.

Returns
-------
out : The base account.
        """
        if self._base_account is None:
            return self._book.root_account
        [x for x in self._base_account.split(os.path.sep) if len(x) > 0]
