"""Binding functions and classes to the GnuCash database."""

import os

from IPython import embed

from sqlalchemy import null
from sqlalchemy import schema as sch
from sqlalchemy import types as sqt
import piecash
from piecash.core.account import AccountType

class DKDatabase:
    """Wrapper around the (modified) GnuCash database."""

    def __init__(self, filename):
        if os.path.exists(filename):
            self.book = piecash.open_book(filename,
                                          readonly=False)
        else:
            self.book = piecash.create_book(sqlite_file=filename)
        self._enrich_database()

    def _enrich_database(self):
        """Add the necessary extra tables if they don't exist yet."""
        conn = self.book.session.connection()
        md = sch.MetaData(bind=conn, reflect=True)
        cred_tab = sch.Table(
            "creditors", md,
            sch.Column('creditor_id', sqt.String, primary_key=True),
            sch.Column('name', sqt.String, nullable=False),
            sch.Column('address1', sqt.String, nullable=False),
            sch.Column('address2', sqt.String),
            sch.Column('address3', sqt.String),
            sch.Column('address4', sqt.String),
            sch.Column('phone', sqt.String),
            sch.Column('email', sqt.String),
            sch.Column('newsletter', sqt.Boolean, default=False,
                       nullable=False),
        )
        contracts_tab = sch.Table(
            "contracts", md,
            sch.Column('contract_id', sqt.String, primary_key=True),
            sch.Column('creditor', sch.ForeignKey("creditors.creditor_id"),
                       nullable=False),
            sch.Column('account', sch.ForeignKey("accounts.guid"),
                       nullable=False),
            sch.Column('date', sqt.DateTime, nullable=False),
            sch.Column('amount', sqt.DECIMAL(2), nullable=False),
            sch.Column('interest', sqt.Float, nullable=False),
            sch.Column('interest_payment', sqt.String, nullable=False),
            sch.Column('version', sqt.String),
            sch.Column('period_type', sqt.String, nullable=False),
            sch.Column('period_notice', sqt.DateTime),
            sch.Column('period_end', sqt.DateTime),
            sch.Column('cancellation_date', sqt.DateTime, default=null()),
            sch.Column('active', sqt.Boolean, nullable=False),
        )
        md.create_all(conn.engine)
        print("DB enriched")


