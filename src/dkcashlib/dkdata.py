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

import sqlalchemy
from sqlalchemy import event, Column, ForeignKey
from sqlalchemy.engine import Engine
from sqlalchemy.ext.automap import automap_base

from . import errors

# foreign_keys setting must be at the very beginning of each connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    pragma = "PRAGMA foreign_keys=ON"
    cursor.execute(pragma)
    cursor.close()

import piecash

import logging; logging.getLogger('sqlalchemy.engine').setLevel('INFO')

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

def _get_table(base, tablename):
    Table = base.classes[tablename]
    Table.object_to_validate = lambda *x: []
    return Table

class DKData:

    account_params = {
        "dk": {"name": "Direktkredite",
               "type": "LIABILITY",
               "placeholder": 1,
               "code": 1000},
        "ausgleich": {"name": "DK-Ausgleich",
                      "type": "ASSET",
                      "description":
                      "Ausgleichskonto für die Direktkredite",
                      "code": 2000},
        "zinsen": {"name": "Direktkreditzinsen",
                   "type": "EXPENSE",
                   "placeholder": 1,
                   "code": 3000},
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
        # print(self._base_dk)
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
        # print("_init_tables")
        # print(self._gnucash_file)
        engine = book.session.connection().engine
        Base = automap_base()
        Base.prepare(engine, reflect=True)

        # Creditors table #####################################################
        if not "creditors" in Base.classes.__dir__():
            # print("Creating creditor")
            class Creditor(Base):
                __tablename__ = "creditors"
                __table_args__ = {'sqlite_autoincrement': True}
                id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
                name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
                address1 = sqlalchemy.Column(sqlalchemy.String, nullable=False)
                address2 = sqlalchemy.Column(sqlalchemy.String)
                address3 = sqlalchemy.Column(sqlalchemy.String)
                address4 = sqlalchemy.Column(sqlalchemy.String)
                phone = sqlalchemy.Column(sqlalchemy.String)
                email = sqlalchemy.Column(sqlalchemy.String)
                newsletter = sqlalchemy.Column(sqlalchemy.Boolean,
                                               nullable=False)

            Creditor.metadata.create_all(bind=engine)
            Base = automap_base()
            Base.prepare(engine, reflect=True)

        # print("Table `creditors` should exist now.")
        # import IPython; IPython.embed()

        # Contracts table #####################################################
        if not "contracts" in Base.classes.__dir__():
            class Contract(Base):
                __tablename__ = "contracts"
                id = Column(sqlalchemy.String, primary_key=True)
                creditor = Column(sqlalchemy.Integer,
                                  ForeignKey('creditors.id'),
                                  nullable=False)
                account = Column(sqlalchemy.String, ForeignKey('accounts.guid'),
                                 nullable=False)
                date = Column(sqlalchemy.String, nullable=False)
                amount = Column(sqlalchemy.Float, nullable=False)
                interest = Column(sqlalchemy.Float, nullable=False)
                interest_payment = Column(sqlalchemy.String, nullable=False)
                version = Column(sqlalchemy.String, nullable=True)
                period_type = Column(sqlalchemy.String, nullable=False)
                period_notice = Column(sqlalchemy.String, nullable=True)
                period_end = Column(sqlalchemy.String, nullable=True)
                cancellation_date = Column(sqlalchemy.String, nullable=True)
                active = Column(sqlalchemy.Boolean, nullable=False)

            Contract.metadata.create_all(bind=engine)
            Base = automap_base()
            Base.prepare(engine, reflect=True)

        # acc1 = Base.classes.accounts(name="Hello")
        # print(acc1.name)

        # print("Table `contracts` should exist now.")
        # import IPython; IPython.embed()


    @_book_open
    def _init_account(self, parent, params, book=None):
        """Initializes the account given by `params`, if it does not exist yet.

If it exists already, do nothing and just return the account.

Parameters
----------
parent : String
    The parent account (fullname).

params : dict
    Parameters defining the account that will be initialized (if it does not
    exist yet).

Returns
-------
out : The account specified by `params`
        """
        # print(parent)
        if parent is None or len(parent) == 0:
            base = book.root_account
        else:
            try:
                base = [x for x in book.accounts
                       if x.fullname == parent][0]
            except IndexError:
                print("Cannot find base account {}.\nAccounts:".format(parent))
                print(list(book.accounts))
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

    @_book_open
    def add_creditor(self, name, address, phone=None, email=None,
                     newsletter=False, book=None):
        """Adds a creditor (person lending money) to the system.

Parameters
----------
name : str

address : iterable
The address consists of an iterable with up to 4 strings, the first one must not
be empty.

phone : str, optional

email : str, optional

newsletter : bool, optional
Whether newsletters shall be sent.  Default is False.

Returns
-------
out : str
The ID of the new creditor.
        """
        engine = book.session.connection().engine
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        Creditor = _get_table(Base, "creditors")
        addr = [""] * 4
        if type(address) == str:
            addr[0] = address
        else:
            addr = [(address[i] if i < len(address) else "")
                    for i in range(len(addr))]
        if len(addr[0]) == 0:
            raise ValueError("Address field must not be empty.")
        creditor = Creditor(name=name, address1=addr[0], address2=addr[1],
                            address3=addr[2], address4=addr[3], phone=phone,
                            email=email, newsletter=newsletter)
        # print("Add creditor")
        book.session.add(creditor)
        # import IPython; IPython.embed()
        book.session.flush()
        return creditor.id

    @_book_open
    def add_contract(self, contract_id, creditor, date, amount, interest,
                     interest_payment="payout", period_type="fixed_duration",
                     period_notice=None, period_end=None, version=None,
                     book=None):
        """Add a contract to the database.

This also adds the correct account, if it does not exist yet.


Parameters
----------
contract_id : int, str
Contract ID, the same as on the written contract.  Must be an integer or string
that can be converted to an integer.

creditor : int
The creditor (id) of this contract.  Must exist.

date : date
Signing date of this contract.

amount : float
Amount (in EUR) of this contract

interest : float
Interest rate for this contract, in percent/year.

interest_payment : str, optional
What shall happen each year with the interest, one of "payout", "cumulative",
"reinvest".  The default is "payout".

period_type : str, optional
The duration type, one of "fixed_duration", "fixed_period_notice",
"initial_plus_n".  Default is "fixed_duration".

period_notice : str, optional
How much in advance the contract needs to be canceled.  The methods requests an
ISO compliant `YYYY-MM-DD` string here, where the less significant parts may be
missing.

period_end : datetime.date, optional

The date at which the contract ends.  The exact meaning depends on the
`period_type` argument.

version : str, optional
Version of the contract form.

Returns
-------
out : None

        """
        engine = book.session.connection().engine
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        Contract = _get_table(Base, "contracts")

        contract_id = int(contract_id)
        # print("Add contract {}".format(contract_id))
        dk_parent_account = book.accounts.get(name="Direktkredite")
        dk_account_name = "DK {:03d}".format(contract_id)
        dk_account_code = "{parent_code}{contract_id:03d}".format(
            parent_code=dk_parent_account.code,
            contract_id=contract_id)
        dk_account = self._init_account(
            parent=dk_parent_account.fullname,
            params={"name": dk_account_name,
                    "code": dk_account_code,
                    "type": "LIABILITY"})
        # Need to flush to get a guid for the account.
        book.flush()

        # import IPython; IPython.embed()
        contract = Contract(
            id=contract_id, creditor=creditor, account=dk_account.guid,
            date=date, amount=amount, interest=interest,
            interest_payment=interest_payment, period_type=period_type,
            period_notice=period_notice, period_end=period_end,
            version=version, cancellation_date=None, active=True)
        # import IPython; IPython.embed()
        book.session.add(contract)

        try:
            book.session.flush()
        except sqlalchemy.exc.IntegrityError as int_err:
            unique_expr = "UNIQUE constraint failed: "
            if unique_expr in int_err.args[0]:
                table_col = int_err.args[0].split(unique_expr)
                table_name, col_name = table_col[-1].split(".")
                exc = errors.DatabaseError(
                    table_name, col_name,
                    "`{}` of `{}` was not unique.".format(
                        col_name, table_name))
                raise exc from int_err
            # Unhandled exception
            raise int_err
