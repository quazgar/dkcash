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
import sys
from warnings import warn

import piecash
import sqlalchemy
from sqlalchemy.ext.automap import automap_base

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

    account_params = {"dk": {"name": "Direktkredite",
                             "type": "LIABILITY",
                             "placeholder": 1},
                      "ausgleich": {"name": "DK-Ausgleich",
                                    "type": "ASSET",
                                    "description":
                                    "Ausgleichskonto für die Direktkredite"},
                      "zinsen": {"name": "Direktkreditzinsen",
                                 "type": "EXPENSE",
                                 "placeholder": 1},
    }
    
    def __init__(self, gnucash_file="dkcash_data.sql",
                 base_dk=None, base_ausgleich=None, base_zinsen=None):
        """Represents the DKCash data.

Parameters
----------
gnucash_file : String, optional
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

        self._base_dk = base_dk
        self._base_ausgleich = base_ausgleich
        self._base_zinsen = base_zinsen
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
        parent_dk = self._init_account(parent=self._base_dk,
                                       params=DKData.account_params["dk"])
        parent_ausgleich = self._init_account(
            parent=self._base_ausgleich,
            params=DKData.account_params["ausgleich"])
        parent_zinsen = self._init_account(
            parent=self._base_zinsen,
            params=DKData.account_params["zinsen"])

    @_book_open
    def _init_tables(self, book=None):
        """Initialize the GnuCash database with extra tables."""
        print("_init_tables")
        print(self._gnucash_file)
        engine = book.session.connection().engine
        Base = automap_base()

        Base.prepare(engine, reflect=True)
        if not "contracts" in Base.classes.__dir__():
            class Contract(Base):
                __tablename__ = "contracts"
                id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
                lender = sqlalchemy.Column(sqlalchemy.String)
            Contract.metadata.create_all(bind=engine)

        # acc1 = Base.classes.accounts(name="Hello")
        # print(acc1.name)

            
        import IPython; IPython.embed()


    @_book_open
    def _init_account(self, parent, params, book=None):
        """Initializes the account given by `params`, if it does not exist yet.

Parameters
----------
parent : String
    The parent account.

params : dict
    Parameters defining the account that will be initialized (if it does not
    exist yet).

Returns
-------
out : The account specified by `params`
        """
        if parent is None or len(parent) == 0:
            base = book.root_account
        else:
            try:
                base = [x for x in book.accounts
                       if x.fullname == parent][0]
            except IndexError:
                print("Cannot find base account {}.".format(parent))
                sys.exit(1)

        # Test if the target account exists already
        name = params["name"]
        try:
            return [child for child in base.children if child.name == name][0]
        except IndexError:
            pass

        # Create and return child account
        EUR = book.commodities.get(mnemonic="EUR")
        acc = piecash.Account(parent=base, commodity=EUR, **params)
        return acc
