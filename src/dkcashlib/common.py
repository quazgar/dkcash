"""Common classes for DKCash.
"""

from . import dkdata
from .dkhandle import Connection

def has_connection(fun):
    """Make sure that a connection exists."""
    def wrapped(self, *args, **kwargs):
        if self.connection is None:
            raise RuntimeError(
                "Connection is None although is needs to be defined for "
                "this method: {}".format(fun))
        return fun(self, *args, **kwargs)
    return wrapped


class Creditor:
    """A creditor is a person who lends money.

    After it is inserted into the database, this object gets a unique ID. Once a
    creditor has an ID, its properties can also be updated in the database.

    """
    def __init__(self, name, address, phone=None, email=None, newsletter=False,
                 connection=None, insert=True):
        """Create a creditor, and may also immediately add it.

        If no ID is given, it will be assigned upon insertion into the database.
        If the ID is not None, it will be saved in this class's object.

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

connection : dkhandle.Connection, optional
    If not given, the Creditor cannot be inserted.

insert : bool, optional
    If the Creditor shall be immediately inserted.  Default is True.
        """
        self.name = name
        if type(address) == str:
            address = [address]
        if len(address) == 0:
            raise ValueError("Adress must not be empty.")
        if len(address) > 4:
            raise ValueError("Adress must consist of at most 4 entries.")
        if address[0] == None or len(address[0]) == 0:
            raise ValueError("First line of address must not be empty.")
        self.address = address
        self.phone = phone
        if newsletter and not email:
            raise ValueError("Newsletter is True, but no email is set.")
        self.email = email
        self.newsletter = bool(newsletter)
        self.connection = connection

        self.creditor_id = None
        if insert:
            self.insert()

    @staticmethod
    def from_namespace(values, connection, insert=False):
        """Create and return a Creditor from a namespace.

By default, do not insert the Creditor because probably it exists already.
        """
        creditor = Creditor(name=values.name,
                            address=(values.address1,
                                     values.address2,
                                     values.address3,
                                     values.address4),
                            phone=values.phone,
                            email=values.email,
                            newsletter=values.newsletter,
                            connection=connection,
                            insert=insert)
        if not creditor.creditor_id:
            creditor.creditor_id = values.id
        return creditor

    @staticmethod
    def find(connection, creditor_id=None, name=None, address=None, phone=None,
             email=None, newsletter=None):
        """Retrieve all matching creditors from the database.

At least one of the specifying arguments must be given.  Only exact matches are
returned.  The address

Returns
-------
A tuple with the found contracts.
        """
        filters = {}
        if creditor_id is not None:
            filters["id"] = creditor_id
        # if creditor is not None:
        #     if isinstance(creditor, Creditor):
        #         creditor = creditor.creditor_id
        #     filters["creditor"] = creditor
        contracts = connection._data.find_creditors(**filters)
        contracts = connection._data.find_contracts(**filters)
        contracts = [Contract.from_namespace(x, connection=connection) for x in
                     contracts]
        return contracts



    @staticmethod
    def retrieve(connection, creditor_id=None, name=None):
        """Retrieve a creditor from the database if a matching one can be found.

At least one of creditor_id or name must be given.  Only exact matches are
returned.

If no match is found, None is returned.
        """
        if creditor_id is None and name is None:
            raise ValueError("At least one of ID and name must be given!")
        filters = {}
        if creditor_id is not None:
            filters["id"] = creditor_id
        if name is not None:
            filters["name"] = name
        query_result = connection._data.find_creditors(**filters)
        if query_result.count() == 0:
            print("No results found.")
            return None
        if query_result.count() > 1:
            print(
"Warning: more than one match found for `{}`, returning only one.".format(
    filters
))
        creditor = Creditor.from_namespace(query_result.first(),
                                           connection=connection)
        return creditor

    @has_connection
    def insert(self):
        """Insert the creditor into the database.

Upon successful insertion, this also assigns the ID.
        """
        creditor_id = self.connection._data.add_creditor(
            self.name, self.address, self.phone, self.email, self.newsletter)
        self.creditor_id = creditor_id

    @has_connection
    def update(self, name=None, address=None, phone=None, email=None,
               newsletter=False):
        """Update the Creditor's properties (those which are not None).

The Creditor must be inserted already in the database, i.e. its ID must not be
None.

Note that address should be a 4 element list.

Returns
-------
out: boolean
True if something was updated, else False.
        """
        address1, address2, address3, address4 = [None] * 4
        if address is not None:
            address1, address2, address3, address4 = address
        updated = self.connection._data.update_creditor(
            self.creditor_id, name=name, phone=phone, email=email,
            newsletter=newsletter,
            address1=address1, address2=address2, address3=address3,
            address4=address4)
        reloaded = self.connection._data.find_creditors(id=self.creditor_id)[0]
        self.name = reloaded.name
        self.address = [reloaded.address1,
                        reloaded.address2,
                        reloaded.address3,
                        reloaded.address4]
        self.phone = reloaded.phone
        self.email = reloaded.email
        self.newsletter = reloaded.newsletter
        return updated

    @has_connection
    def delete(self, delete_contracts=False):
        """Delete this creditor from the database.

Parameters
----------
delete_contracts : bool, optional
    If contracts by this Creditor shall also be deleted.  Default is False.  If
    False, an exception is raised if there are any contracts by this Creditor.
        """
        linked_contracts = Contract.find(self.connection, creditor=self)
        print("linked:")
        print(linked_contracts)
        if linked_contracts:
            if delete_contracts:
                for contract in linked_contracts:
                    print("Warning, deleting contract: {}".format(contract))
                    contract.delete()
            else:
                raise RuntimeError(
                    "Deleting the creditor {} failed, because there are still "
                    "contracts linked to the creditor.".format(self))

        self.connection._data.delete_creditor(creditor_id=self.creditor_id)


class Contract:
    """A contract is connected to a creditor.

The Contract ID is the same as on the written contract, it must be a unique
integer (or can be converted to an integer).

Implementation
--------------

Internally, a ``Contract`` consists mainly of a sequence of states, orderd by
date.  Each state is completely self-sufficient, so no prior states necessary to
infer any information.  If there is no state stored for a certain time, the
parameters (run time, interest rate, etc.) of the contract do not change,
although the accumulated interest may change over time of course.

    """

    def __init__(self, contract_id, creditor, date, amount, interest,
                 interest_payment="payout", period_type="fixed_duration",
                 period_notice=None, period_end=None, version=None,
                 cancellation_date=None,
                 connection=None, insert=True):
        """Create a contract, and optionally also immediately add it.

If no ID is given, it will be assigned upon insertion into the database.

Parameters
----------
contract_id : int, str
Contract ID, the same as on the written contract.  Must be an integer or string
that can be converted to an integer.

creditor : Creditor
The creditor of this contract.  If it is not inserted yet, will be inserted
together with the contract.

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

        """
        if not str(int(contract_id)) == str(contract_id):
            raise ValueError(
                "`contract_id` must be an int or losslessly convertible")
        self.contract_id = int(contract_id)
        if type(creditor) == int:
            self.creditor_id = creditor
        else:
            self.creditor_id = creditor.creditor_id
        self._initial_state = _State(
            date=date, amount=amount, interest=interest, interest_payment=interest_payment,
            period_type=period_type, period_notice=period_notice, period_end=period_end,
            cancellation_date=cancellation_date, version=version)
        self._states = {date: self._initial_state}
        self.connection=connection
        self._validate_attributes()

        if insert:
            self.insert()

    def _validate_attributes(self):
        """Validate the attributes, especially for the different period types.

Raise exceptions or print warnings for invalid or unusual attributes.
        """
        assert self.creditor_id is not None

    @has_connection
    def insert(self):
        """Insert the Contract into the database."""

        self.connection._data.add_contract(
            contract_id=self.contract_id, creditor=self.creditor_id,
            date=self.date, amount=self.amount, interest=self.interest,
            interest_payment=self.interest_payment, period_type=self.period_type,
            period_notice=self.period_notice, period_end=self.period_end,
            version=self.version)

    @staticmethod
    def from_namespace(values, connection, insert=False):
        """Create and return a Contract from a namespace.

By default, do not insert the Contract because probably it exists already.
        """
        # for k, v in values.__dict__.items():
        #     print("{}:\t{}".format(k,v))
        contract = Contract(contract_id=values.id,
                            creditor=values.creditor,
                            date=values.date,
                            amount=values.amount,
                            interest=values.interest,
                            interest_payment=values.interest_payment,
                            period_type=values.period_type,
                            period_notice=values.period_notice,
                            period_end=values.period_end,
                            version=values.version,
                            cancellation_date=values.cancellation_date,
                            connection=connection, insert=insert)
        return contract

    @staticmethod
    def retrieve(connection, contract_id=None,  creditor_id=None):
        """Retrieve a contract from the database if a matching one can be found.

At least one of the specifying arguments must be given.  Only exact matches are
returned.  If more than one contract fits the given criteria, a RuntimeError is
raised.

If no match is found, None is returned.
        """
        if contract_id is None and creditor_id is None:
            raise ValueError("At least one of the two IDs must be given!")
        filters = {}
        if contract_id is not None:
            filters["id"] = contract_id
        if creditor_id is not None:
            filters["creditor"] = creditor_id
        query_result = connection._data.find_contracts(**filters)
        if query_result.count() == 0:
            print("No results found.")
            return None
        if query_result.count() > 1:
            raise RuntimeError(
                "Warning: more than one match found for `{}`.".format(filters))
        contract = Contract.from_namespace(query_result.first(),
                                           connection=connection)
        return contract

    @staticmethod
    def find(connection, contract_id=None, creditor=None, date=None,
             amount=None, interest=None, interest_payment=None,
             period_type=None, period_notice=None, period_end=None,
             version=None):
        """Retrieve all matching contracts from the database.

At least one of the specifying arguments must be given.  Only exact matches are
returned.

Returns
-------
A tuple with the found contracts.
        """
        filters = {}
        if contract_id is not None:
            filters["id"] = contract_id
        if creditor is not None:
            if isinstance(creditor, Creditor):
                creditor = creditor.creditor_id
            filters["creditor"] = creditor
        contracts = connection._data.find_contracts(**filters)
        contracts = [Contract.from_namespace(x, connection=connection) for x in
                     contracts]
        return contracts

    def update(self, contract_id=None, creditor=None, date=None, amount=None,
               interest=None, interest_payment=None, period_type=None,
               period_notice=None, period_end=None, version=None,
               cancellation_date=None, active=None):
        """Update the Contract's properties (those which are not None).

The Contract must be inserted already in the database.

Note that this "retroactively" changes all values without noting the date of
change, which may not always be what you want.  For example for changing the
interest rate at a later time, it may be better to cancel the contract and
create a new contract instead.

Returns
-------
out: boolean
True if something was updated, else False.
        """
        if isinstance(creditor, Creditor):
            creditor_id = creditor.creditor_id
        else:
            creditor_id = creditor

        updated = self.connection._data.update_contract(
            self.contract_id,
            creditor=creditor_id, date=date,
            amount=amount, interest=interest,
            interest_payment=interest_payment,
            period_type=period_type,
            period_notice=period_notice,
            period_end=period_end,
            version=version,
            cancellation_date=cancellation_date,
            active=active)
        reloaded = self.connection._data.find_contracts(id=self.contract_id)[0]
        self.creditor_id = reloaded.creditor
        self.date = reloaded.date
        self.amount = reloaded.amount
        self.interest = reloaded.interest
        self.interest_payment = reloaded.interest_payment
        self.interest_payment = reloaded.interest_payment
        self.period_type = reloaded.period_type
        self.period_notice = reloaded.period_notice
        self.period_end = reloaded.period_end
        self.cancellation_date = reloaded.cancellation_date
        self.version = reloaded.version

        return updated

    def delete(self):
        """Delete this Contract from the database.

Returns
----------
out : int
    The creditor ID of this contract.
        """
        self.connection._data.delete_contract(contract_id=self.contract_id)
        return self.creditor_id


class _State:
    def __init__(self, date, amount, interest, interest_payment="payout",
                 period_type="fixed_duration", period_notice=None,
                 period_end=None, version=None, cancellation_date=None,
                 balance=0.0):
        self.date = date
        self.amount = amount
        self.interest = interest
        self.interest_payment = interest_payment
        self.period_type = period_type
        self.period_notice = period_notice
        self.period_end = period_end
        self.version = version
        self.cancellation_date = cancellation_date
        self.balance = balance

    def _validate_attributes(self):
        """Validate the attributes, especially for the different period types.

Raise exceptions or print warnings for invalid or unusual attributes.
        """
        assert self.date is not None
        assert self.amount is not None
        assert self.amount >= 0.0
        assert self.balance is not None
        assert self.balance >= 0.0
        assert self.interest is not None
        assert self.interest >= 0.0
        assert self.interest_payment in ("payout", "cumulative", "reinvest")
        if self.period_type == "fixed_duration":
            if self.period_end is None:
                raise ValueError('If "period type" is `fixed_duration`, '
                                 '`period_end` must be given.')
            if self.period_notice is not None:
                print("Warning, `period_notice` has no effect for fixed "
                      "duration period type.")
        elif self.period_type == "fixed_period_notice":
            if self.period_notice is None:
                raise ValueError('If "period type" is `fixed_period_notice`, '
                                 '`period_notice` must be given.')
            if self.period_end is not None:
                print('Warning, `period_end` has no effect for period type '
                      '"fixed period notice".')
        elif self.period_type == "initial_plus_n":
            if self.period_notice is None:
                raise ValueError('If "period type" is `initial_plus_n`, '
                                 '`period_notice` must be given.')
            if self.period_end is None:
                raise ValueError('If "period type" is `initial_plus_n`, '
                                 '`period_end` must be given.')
        else:
            raise ValueError("Unknown `period_type` argument.")

