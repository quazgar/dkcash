"""Common classes for DKCash.
"""

import dkdata

class Connection:
    """Connection to the database/GnuCash file.

    This class can be used to conveniently add or modify data, search for
    records, generate reports.

    Implementation notice: This class internally connects to dkdata.DKData.

    """

    def __init__(self, gnucash_file="dkcash_data.sql",
                 base_dk=None, base_ausgleich=None, base_zinsen=None):
        """Create a DKCash connection.

The constructor needs information about where to store data, and how to interact
with existing account structures.

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
        self._data = dkdata.DKData( gnucash_file=gnucash_file, base_dk=base_dk,
                                    base_ausgleich=base_ausgleich,
                                    base_zinsen=base_zinsen)

    ###########################################################################
    # The following methods are just some ideas what should be(come) possible #
    ###########################################################################

    def find_creditors(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def find_contracts(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def calculate_interests(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def generate_report(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def generate_spreadsheet(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def next_due_dates(self, **kwargs):
        """The dates when the next accounts are due."""
        raise NotImplemented("API and behaviour not defined yet")

    def generate_account_statements(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")

    def average_interest(self, **kwargs):
        raise NotImplemented("API and behaviour not defined yet")


class Creditor:
    """A creditor is a person who lends money.

    After it is inserted into the database, this object gets a unique ID. Once a
    creditor has an ID, its properties can also be updated in the database.

    """
    def __init__(self, name, address, phone=None, email=None, newsletter=False,
                 connection=None, insert=True):
        """Create a creditor, and may also immediately add it.

        If no ID is given, it will be assigned upon insertion into the database.
        If the ID is not None, it

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

        """
        raise NotImplemented()

    def save(self, connection=None):
        """Inserts the creditor into the database.

        Upon success, this also assigns the ID.

        """
        raise NotImplemented()
        
    def update(self, name=None, address=None, phone=None, email=None,
               newsletter=False):
        """Updates the Creditor's properties (those which are not None).

        The Creditor must be inserted already in the database, i.e. its ID must
        not be None.

        """
        raise NotImplemented()

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
        raise NotImplemented()
