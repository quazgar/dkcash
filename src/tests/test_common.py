"""Test contract insertion.

Call e.g. with `pytest` (for Python3).
"""

# import argparse
# import os
# import pathlib2
import pytest
# import sys
import unittest

# from datetime import date
# from dkcashlib import dkdata, errors
from dkcashlib import common


@pytest.fixture
def connection(tmp_path):
    filename = tmp_path / "test.gnucash"
    conn = common.Connection(gnucash_file=str(filename))
    return conn

def test_connection(connection):
    assert type(connection) == common.Connection
    assert connection._data._gnucash_file.endswith("test.gnucash")


def test_creditor(connection):
    with unittest.TestCase().assertRaises(ValueError):
        creditor = common.Creditor("Donald Duck", [], insert=False)
    creditor_donald = common.Creditor(
        "Donald Duck", ["Entengasse 5", "12345 Entenhausen"],
        connection=connection)
    assert creditor_donald.creditor_id is not None
    creditor_dagobert = common.Creditor(
        "Dagobert Duck", ["Entengasse 5", "12345 Entenhausen"],
        connection=connection, insert=False)
    assert creditor_dagobert.creditor_id is None
    creditor_dagobert.insert()
    assert creditor_dagobert.creditor_id is not None

    new_phone = "+4987654321"
    creditor_dagobert.update(phone=new_phone)
    assert creditor_dagobert.phone == new_phone

    new_address = ["Geldspeicher 1", "12345 Entenhausen", "", ""]
    creditor_dagobert.update(address=new_address)
    assert creditor_dagobert.address == new_address

def test_contract(connection):
    pass
