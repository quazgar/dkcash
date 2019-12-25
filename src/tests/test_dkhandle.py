#!/usr/bin/env pytest
"""Test the dkhandle module.

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


@pytest.fixture
def connection(tmp_path):
    filename = tmp_path / "test.gnucash"
    conn = dkhandle.Connection(gnucash_file=str(filename))
    return conn


def test_connection(connection):
    assert type(connection) == common.Connection
    assert connection._data._gnucash_file.endswith("test.gnucash")


def test_contract(connection):
    pass
