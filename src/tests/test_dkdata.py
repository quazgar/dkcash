#!/usr/bin/env pytest
"""Test contract insertion.

Call e.g. with `pytest` (for Python3).
"""

import argparse
import os
import pathlib2
import pytest
import sys
import unittest

from datetime import date
from dkcashlib import dkdata, errors


@pytest.fixture
def data(tmp_path):
    filename = tmp_path / "test.gnucash"
    print(filename)
    data = dkdata.DKData(gnucash_file=str(filename))
    return data

def test_dkdata_add_creditor(data):
    print(data)
    creditor_id = data.add_creditor(
        "Someone", ["address line 1", "address line 2"],
        phone="+491234567890", email="hallo@example.com")

def test_dkdata_add_contract(data):
    print(data)
    creditor_id = data.add_creditor(
        "Someone", ["address line 1", "address line 2"],
        phone="+491234567890", email="hallo@example.com")
    data.add_contract("2038", creditor_id, date="2001-01-01", amount=1234.56,
                      interest=0.1, period_end=date(2000, 1, 1))
    with unittest.TestCase().assertRaises(errors.DatabaseError):
        data.add_contract("2038", creditor_id, date="2002-02-02", amount=0.01,
                          interest=0.0, period_end=date(2003, 3, 3))

