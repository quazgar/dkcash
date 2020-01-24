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


def _extract_like(**kwargs):
    """Split the arguments into "normal" and "LIKE"-like arguments.

Returns
-------

verbatim_filters: dict
    The "normal" arguments.

like_filters: dict
    The "LIKE"-like arguments, with `*` replaced by `%`.
    """
    verbatim_filters = {}
    like_filters = {}
    for key, value in kwargs.items():
        if isinstance(value, str) and "*" in value:
            like_value = value.replace("*", "%")
            like_filters[key] = like_value
        else:
            verbatim_filters[key] = value
    return verbatim_filters, like_filters


def _filter_flexible(query, smap, **kwargs):
    """Apply `kwargs` as additional filters to the query.

Parameters
----------
query: Query
The Query to be filtered.

smap: sqlalchemy map class
The class in whose context the kwargs are to be interpreted.

kwargs:
_extract_like() is used to split these into exact and pattern matching values.


Returns
-------
query: Query
Filtered Query object.
    """
    verbatim_filters, like_filters = _extract_like(**kwargs)
    columns =smap.__dict__
    likes = [columns[key].like(value) for key, value in like_filters.items()]
    filtered_query = query.filter_by(**verbatim_filters).filter(*likes)
    return filtered_query


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
    def update_creditor(self, creditor_id,
                        name=None, phone=None, email=None,
                        newsletter=None, address1=None, address2=None,
                        address3=None, address4=None, book=None):
        """Updates the creditor's entry in the database.

Returns
-------
out: boolean
True if something was updated, else False.
        """
        creditor = self.find_creditors(id=creditor_id)[0]
        update = False
        if name is not None:
            creditor.name = name
            update = True
        if address1 is not None:
            creditor.address1 = address1
            update = True
        if address2 is not None:
            creditor.address2 = address2
            update = True
        if address3 is not None:
            creditor.address3 = address3
            update = True
        if address4 is not None:
            creditor.address4 = address4
            update = True
        if phone is not None:
            creditor.phone = phone
            print(creditor.phone)
            update = True
        if email is not None:
            creditor.email = email
            update = True
        if newsletter is not None:
            creditor.newsletter = newsletter
            update = True
        if update:
            book.session.commit()
            book.session.flush()
            print(creditor)
        return update

    @_book_open
    def find_creditors(self, book=None, **kwargs):
        """Find creditors matching the given filters.

Parameters
----------

**kwargs : SqlAlchemy filters
    Filters which are passed on to SqlAlchemy's `filter_by` method:
    https://docs.sqlalchemy.org/en/13/orm/query.html#sqlalchemy.orm.query.Query.filter_by
    Normally, string filter values are interpreted verbatim, but if they contain
    a `*`, they are interpreted as `LIKE` pattern expressions and matched
    accordingly.

Returns
-------
out : Query
An iterable of contracts (automapped by SqlAlchemy).
        """
        engine = book.session.connection().engine
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        Creditor = _get_table(Base, "creditors")
        if "address" in kwargs:
            raise NotImplementedError(
                "Special handling for generic address expr not implemented.")
        filtered = _filter_flexible(book.session.query(Creditor), Creditor,
                                    **kwargs)
        return filtered

    @_book_open
    def delete_creditor(self, creditor_id, book=None):
        """Remove this creditor from the database."""
        deleted = self.find_creditors(id=creditor_id).delete()
        if deleted >= 2:
            raise RuntimeError("Deleted more than one creditor, but only one "
                               "should have existed.")
        if deleted == 0:
            raise ValueError("Tried to delete non-existent creditor.")

    @_book_open
    def add_contract(self, contract_id, creditor, date, amount, interest,
                     interest_payment="payout", period_type="fixed_duration",
                     period_notice=None, period_end=None, version=None,
                     cancellation_date=None, book=None):
        """Add a contract to the database.

This also adds the correct account to GnuCash, if it does not exist yet.


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

cancellation_date : datetime.date, optional
The last date on which the contract is active, e.g. after a cancellation.

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
            version=version, cancellation_date=cancellation_date, active=False)
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

    @_book_open
    def update_contract(self, contract_id, creditor=None, date=None,
                        amount=None, interest=None, interest_payment=None,
                        period_type=None, period_notice=None, period_end=None,
                        version=None, cancellation_date=None, active=None,
                        book=None):
        """Updates the contract's entry in the database.

Returns
-------
out: boolean
True if something was updated, else False.
        """
        contract = self.find_contracts(id=contract_id)[0]
        update = False
        if creditor is not None:
            contract.creditor = creditor
            update = True
        if date is not None:
            contract.date = date
            update = True
        if amount is not None:
            contract.amount = amount
            update = True
        if interest is not None:
            contract.interest = interest
            update = True
        if interest_payment is not None:
            contract.interest_payment = interest_payment
            update = True
        if period_type is not None:
            contract.period_type = period_type
            update = True
        if period_notice is not None:
            contract.period_notice = period_notice
            update = True
        if period_end is not None:
            contract.period_end = period_end
            update = True
        if version is not None:
            contract.version = version
            update = True
        if cancellation_date is not None:
            contract.cancellation_date = cancellation_date
            update = True
        if active is not None:
            contract.active = active
            update = True
        if update:
            book.session.commit()
            book.session.flush()
            print(creditor)
        return update


    @_book_open
    def find_contracts(self, book=None, **kwargs):
        """Find contracts matching the given filters.

Parameters
----------

**kwargs : SqlAlchemy filters
    Filters which are passed on to SqlAlchemy's `filter_by` method:
    https://docs.sqlalchemy.org/en/13/orm/query.html#sqlalchemy.orm.query.Query.filter_by
    Normally, string filter values are interpreted verbatim, but if they contain
    a `*`, they are interpreted as `LIKE` pattern expressions and matched
    accordingly.


Returns
-------
out : Query
An iterable of contracts (automapped by SqlAlchemy).
             """
        engine = book.session.connection().engine
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        Contract = _get_table(Base, "contracts")
        filtered = _filter_flexible(book.session.query(Contract), Contract,
                                    **kwargs)
        return filtered

    @_book_open
    def delete_contract(self, contract_id, book=None):
        """Remove this contract from the database."""
        deleted = self.find_contracts(id=contract_id).delete()
        if deleted >= 2:
            raise RuntimeError("Deleted more than one contract, but only one "
                               "should have existed.")
        if deleted == 0:
            raise ValueError("Tried to delete non-existent contract.")
