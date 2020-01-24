#!/usr/bin/env pytest
"""Test common operations.

Call e.g. with `pytest` (for Python3).
"""

import datetime
# import os
# import pathlib2
import pytest
import random
import sys
import unittest

# from datetime import date
# from dkcashlib import dkdata, errors
from dkcashlib import common
from dkcashlib import dkhandle

from dkcashlib.common import Creditor, Contract

@pytest.fixture
def connection(tmp_path):
    filename = tmp_path / "test.gnucash"
    conn = dkhandle.Connection(gnucash_file=str(filename))
    return conn

def _create_contract(creditor, connection, number=None):
    """Create and return a different contract for different numbers."""
    if number is None:
        number = random.randint(0, sys.maxsize)
    contract_id = number
    date = "2019-01-{}".format(number % 31 + 1)
    amount = number / 100
    interest = number % 10 / 10
    interest_payment = "reinvest"
    period_type="initial_plus_n"
    period_notice = "1-06" # 1 year 6 months
    period_end = datetime.date.today()
    version = "1.0"

    contract = Contract(
        contract_id=contract_id, creditor=creditor, date=date, amount=amount,
        interest=interest, interest_payment=interest_payment,
        period_type=period_type, period_notice=period_notice,
        period_end=period_end, version=version, connection=connection,
        insert=False)

    return contract


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

    # Creating a Creditor from a namespace.
    query_result = connection._data.find_creditors(name="Dagobert Duck")
    assert query_result.count() == 1
    dagobert_dup = Creditor.from_namespace(query_result.first(),
                                           connection=connection)
    assert dagobert_dup.creditor_id == creditor_dagobert.creditor_id


def test_creditor_retrieval(connection):
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


def test_creditor_delete(connection):
    """Test if deletion works."""
    # Set up creditor
    address = ("Geldspeicher 1", "12345 Entenhausen", "", "")
    creditor_dagobert = Creditor(
        "Dagobert Duck", address,
        connection=connection, insert=True)
    assert creditor_dagobert.creditor_id is not None

    # Delete creditor
    creditor_id = creditor_dagobert.creditor_id
    creditor_dagobert.delete()

    # Insert again, add contract, then delete both
    creditor_dagobert.insert()
    contract = _create_contract(creditor_dagobert, connection=connection)
    contract.insert()
    with unittest.TestCase().assertRaises(RuntimeError):
        creditor = creditor_dagobert.delete()
    creditor_dagobert.delete(delete_contracts=True)

    # Try to retrieve it again
    retrieved = Creditor.retrieve(connection=connection,
                                  creditor_id=creditor_id)
    assert retrieved is None

    # Deleting a second time should not work
    with unittest.TestCase().assertRaises(ValueError):
        creditor = creditor_dagobert.delete()

    creditor_no_connection = Creditor("No Connection", address, insert=False)
    with unittest.TestCase().assertRaises(RuntimeError):
        creditor = creditor_no_connection.delete()


def test_contract(connection):
    """Test creation and insertion of contracts."""
    address = ("Geldspeicher 1", "12345 Entenhausen", "", "")
    creditor = Creditor("Dagobert Duck", address, connection=connection)
    contract_id = "4223"
    date = "2019-01-01"
    amount = 3.1416e12
    interest = 20.0
    interest_payment = "reinvest"
    period_type="initial_plus_n"
    period_notice = "1-06" # 1 year 6 months
    period_end = datetime.date.today()
    version = "1.0"

    contract_local = Contract(
        contract_id=contract_id, creditor=creditor, date=date, amount=amount,
        interest=interest, interest_payment=interest_payment,
        period_type=period_type, period_notice=period_notice,
        period_end=period_end, version=version, connection=connection,
        insert=False)
    assert (Contract.retrieve(connection=connection, contract_id=contract_id)
            is None)
    contract_local.insert()

    retrieved = Contract.retrieve(connection=connection,
                                  contract_id=contract_id)
    assert retrieved is not None
    assert retrieved.amount == amount

    with unittest.TestCase().assertRaises(RuntimeError):
        # Inserting the same contract ID again.
        retrieved.insert()

    new_amount = 23.00
    print(retrieved)
    retrieved.update(amount=new_amount)

    new_retrieved = Contract.retrieve(connection=connection,
                                      contract_id=contract_id)
    assert new_retrieved is not None
    assert new_retrieved.amount == new_amount

    new_retrieved.delete()
    assert (Contract.retrieve(connection=connection, contract_id=contract_id)
            is None)

