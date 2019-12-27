#!/usr/bin/env pytest
"""Test common operations.

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
from dkcashlib import dkhandle

from dkcashlib.common import Creditor

@pytest.fixture
def connection(tmp_path):
    filename = tmp_path / "test.gnucash"
    conn = dkhandle.Connection(gnucash_file=str(filename))
    return conn


def test_creditor(connection):
    with unittest.TestCase().assertRaises(ValueError):
        creditor = Creditor("Donald Duck", [], insert=False)
    creditor_donald = Creditor(
        "Donald Duck", ["Entengasse 5", "12345 Entenhausen"],
        connection=connection)
    assert creditor_donald.creditor_id is not None
    creditor_dagobert = Creditor(
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

    # Retrieve and recreate
    query_result = connection._data.find_creditors(name="Dagobert Duck")
    assert query_result.count() == 1
    dagobert_dup = Creditor.from_namespace(query_result.first(),
                                           connection=connection)
    assert dagobert_dup.creditor_id == creditor_dagobert.creditor_id

def test_retrieval(connection):
    """Test if retrieval works."""

    # Set up creditor
    address = ("Geldspeicher 1", "12345 Entenhausen", "", "")
    creditor_dagobert = Creditor(
        "Dagobert Duck", address,
        connection=connection, insert=False)
    assert creditor_dagobert.creditor_id is None
    creditor_dagobert.insert()

    # Retrieve one of the inserted creditors
    dago_id = creditor_dagobert.creditor_id
    dago_name = creditor_dagobert.name

    retrieved = Creditor.retrieve(connection, creditor_id=dago_id)
    assert retrieved is not None
    assert retrieved.name == dago_name

    retrieved = Creditor.retrieve(connection, name=dago_name)
    assert retrieved is not None
    assert retrieved.creditor_id == dago_id

    retrieved = Creditor.retrieve(connection, creditor_id=dago_id,
                                  name=dago_name)
    assert retrieved is not None
    assert retrieved.address == address

def test_contract(connection):
    pass
