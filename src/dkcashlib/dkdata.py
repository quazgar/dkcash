"""This module handles the backend database.

Use it as the connecting layer to a GnuCash database.  This module only does
"dumb" transactions, for more high-level needs, use the `dkhandle` module.

Because the same Sqlite GnuCash file is used for GnuCash specific operations
(account and transactions) and for storing loan specific information, frequent
opening and closing of the database connection on demand may be necessary.
"""

import functools
import inspect
import os
from warnings import warn

import piecash

_open_books = dict()

# Possibly better implementation, as a class again:
# https://stackoverflow.com/questions/30104047/how-can-i-decorate-an-instance-method-with-a-decorator-class
def _book_open(func):
    """Each book must be open only once at a time."""
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        # print("self: {self}\n*args: {args}\nkwargs: {kwargs}".format(
        #     self=self, args=args, kwargs=kwargs))
        # Get the normalized book filename.
        filename = self._gnucash_file
        filename = os.path.abspath(filename)

        # Default case: Book was opened already
        if filename in _open_books:
            # print("    Not opening {} again for {}.".format(filename,
            #                                             func.__name__))
            kwargs.update({"book": _open_books[filename]})
            result = func(self, *args, **kwargs)
        else:
            # Now the book is opened, the function called, then the book is
            # saved and closed automatically.  Also the book is added to the
            # list of open books and removed at the end.
            with piecash.open_book(filename, readonly=False) as book:
                # print("Opened {} for {}".format(filename, func.__name__))
                _open_books[filename] = book
                kwargs.update({"book": book})
                result = func(self, *args, **kwargs)
                # print("Saving and closing {}".format(filename))
                book.save()
                _open_books.pop(filename)
        return result

    return wrap

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
    not yet exist.  This is a colon-separated string, for example
    `Aktiva:DKVerwaltung`.
"""

        self._gnucash_file = gnucash_file
        if not os.path.exists(gnucash_file):
            self._create_gnucash_file()

        self._base_account = base_account
        self._init_gnucash()
        self._init_tables()

    def _create_gnucash_file(self):
        """Creates the GnuCash file for this DKData object.

The GnuCash file must not exist yet."""
        new_book = piecash.create_book(self._gnucash_file)
        new_book.close()

    @_book_open
    def _init_gnucash(self, book=None):
        """Initialize the GnuCash database with the necessary accounts."""
        EUR = book.commodities.get(mnemonic="EUR")
        parent = self._get_base_account()
        print(parent)
        acc_direktkredite

    def _init_tables(self):
        """Initialize the GnuCash database with extra tables."""
        print("_init_tables")

    @_book_open
    def _get_base_account(self, book=None):
        """Returns the base account for this object.

Returns
-------
out : The base account, or None if if there is no such account.
        """
        if self._base_account is None or len(self._base_account) == 0:
            return book.root_account

        try:
            acc = [x for x in book.accounts
                   if x.fullname == self._base_account][0]
        except IndexError:
            return None

        # Base account found
        return acc
