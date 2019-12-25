"""Classes to handle connections, the database, high-level methods.
"""

from . import dkdata

class Connection:
    """Connection to the database/GnuCash file.

This class can be used to conveniently add or modify data, search for records,
generate reports.

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
        raise NotImplementedError("API and behaviour not defined yet")

    def find_contracts(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")

    def calculate_interests(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")

    def generate_report(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")

    def generate_spreadsheet(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")

    def next_due_dates(self, **kwargs):
        """The dates when the next accounts are due."""
        raise NotImplementedError("API and behaviour not defined yet")

    def generate_account_statements(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")

    def average_interest(self, **kwargs):
        raise NotImplementedError("API and behaviour not defined yet")
