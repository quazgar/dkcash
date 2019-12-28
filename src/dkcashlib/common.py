"""Common classes for DKCash.
"""

from . import dkdata
from .dkhandle import Connection


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

    def insert(self, connection=None):
        """Inserts the creditor into the database.

Upon successful insertion, this also assigns the ID.
"""
        if connection is not None:
            self.connection = connection
        if self.connection is None:
            raise RuntimeError(
                "Connection is None although is needs to be defined for "
                "inserting this object into the database.")
        creditor_id = self.connection._data.add_creditor(
            self.name, self.address, self.phone, self.email, self.newsletter)
        self.creditor_id = creditor_id

    def update(self, name=None, address=None, phone=None, email=None,
               newsletter=False):
        """Updates the Creditor's properties (those which are not None).

The Creditor must be inserted already in the database, i.e. its ID must not be
None.

Note that address should be a 4 element list.

        """
        address1, address2, address3, address4 = [None] * 4
        if address is not None:
            address1, address2, address3, address4 = address
        self.connection._data.update_creditor(
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

    def delete(self, delete_contracts=False):
        """Deletes this creditor from the database.

Parameters
----------
delete_contracts : bool, optional
    If contracts by this Creditor shall also be deleted.  Default is False.
"""
        raise NotImplementedError("TODO: Need to check for contracts.")
        if self.connection is None:
            raise RuntimeError(
                "Connection is None although is needs to be defined for "
                "deleting this object from the database.")
        self.connection._data.delete_creditor(creditor_id=self.creditor_id)


class Contract:
    """A contract is connected to a creditor.

The Contract ID is the same as on the written contract, it must be a unique
integer (or can be converted to an integer).

    """
    def __init__(self, contract_id, creditor, date, amount, interest,
                 interest_payment="payout", period_type="fixed_duration",
                 period_notice=None, period_end=None, version=None,
                 connection=None, insert=True):
        """Create a contract, and may also immediately add it.

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
        """
        raise NotImplementedError()
