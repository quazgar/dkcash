"""Binding functions and classes to the GnuCash database.

Implementation notes
--------------------

Piecash requires SqlAlchemy classes to have a few special methods,
e.g. `object_to_validate`.  This probably means that content similar to
`sa_extra` module should be used, this is provided by the piecash_compat module.

"""

import os
import uuid
import datetime

from IPython import embed

from sqlalchemy import (null,
                        Column, ForeignKey,
                        Boolean, DateTime, DECIMAL, Float, Integer, String,
                        )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression as sqe
from sqlalchemy import schema as sch
from sqlalchemy import types as sqt
import piecash

from piecash.core.account import AccountType, Account

from .piecash_compat import DeclarativeBase as PCCDeclarativeBase

class DKDatabase:
    """Wrapper around the (modified) GnuCash database."""
    def __init__(self, filename, sample_entries=False):
        if os.path.exists(filename):
            print("Opening GnuCash database.")
            self.book = piecash.open_book(filename,
                                          readonly=False)
        else:
            print("Creating GnuCash database.")
            self.book = piecash.create_book(sqlite_file=filename)
        self._enrich_database()
        if sample_entries:
            print("Adding sample entries.")
            self._add_sample_entries()
        # embed()

    def _enrich_database(self):
        """Add the necessary extra accounts and tables if necessary."""
        self._init_accounts()
        session = self.book.session
        conn = session.connection()
        md = sch.MetaData(bind=conn, reflect=True)
        Base = declarative_base(bind=conn, metadata=md)

        class Creditor(Base):
            __tablename__ = "creditors"
            __table_args__ = {'extend_existing': True}
            creditor_id = Column(String, primary_key=True)
            name = Column(String, nullable=False)
            address1 = Column(String, nullable=False)
            address2 = Column(String)
            address3 = Column(String)
            address4 = Column(String)
            phone = Column(String)
            email = Column(String)
            newsletter = Column(Boolean, default=False, nullable=False)

        class Contract(Base):
            __tablename__ = "contracts"
            __table_args__ = {'extend_existing': True}
            contract_id = Column(String, primary_key=True)
            creditor = Column(ForeignKey("creditors.creditor_id"),
                              nullable=False)
            account = Column(ForeignKey("accounts.guid"), nullable=False)
            date = Column(DateTime, nullable=False)
            amount = Column(DECIMAL(2), nullable=False)
            interest = Column(Float, nullable=False)
            interest_payment = Column(String, nullable=False)
            version = Column(String)
            period_type = Column(String, nullable=False)
            period_notice = Column(DateTime)
            period_end = Column(DateTime)
            cancellation_date = Column(DateTime, default=null())
            active = Column(Boolean, nullable=False)

        Base.metadata.create_all(conn.engine)

        print("DB enriched")

    def _init_accounts(self):
        EUR = self.book.commodities.get(mnemonic="EUR")
        self._conditional_add_account(
            name="Direktkredite",
            code="10000",
            placeholder=True)
        self._conditional_add_account(
            name="DK-Herkunft",
            code="20000",
        )
        self._conditional_add_account(
            name="Kreditzinsen",
            type="INCOME",
            code="30000",
        )
        self.book.save()

    def _conditional_add_account(self, name,
                                 type="ASSET", parent=None, commodity="EUR",
                                 code=None, placeholder=True):
        if parent is None:
            parent = self.book.root_account
        query = self.book.session.query(Account).filter(
            Account.name.like("%{}".format(name)),
            Account.type==type,
            Account.parent==parent)
        if query.count() == 1:
            return
        comm = self.book.commodities.get(mnemonic=commodity)
        acc = Account(name=name, type=type, parent=parent, commodity=comm,
                      code=code, placeholder=placeholder)
        print("Creating account {name}".format(name=name))
        self.book.save()

    def _add_sample_entries(self):
        session = self.book.session
        conn = session.connection()
        Base = automap_base(declarative_base=PCCDeclarativeBase)
        Base.prepare(conn.engine, reflect=True)

        Creditor = Base.classes.creditors
        Contract = Base.classes.contracts
        # Add a creditor and two contracts
        cred1 = Creditor(
            creditor_id=str(uuid.uuid4()),
            name="Newly newt",
            address1="New Street 1",
            address2="12345 Irgendwo",
            newsletter=True
        )
        dk_account = self.book.session.query(Account).filter(
            Account.name.like("%Direktkredite")).first()
        # print(dk_account)
        contr1 = Contract(
            contract_id="23",
            creditor=cred1.creditor_id,
            account=dk_account.guid,
            date=datetime.date.today(),
            amount=3.14,
            interest=0.00,
            interest_payment="never",
            version="0.1",
            period_type="NONE",
            period_notice=datetime.date.today(),
            period_end=datetime.date.today(),
            cancellation_date=datetime.date.today(),
            active=True
        )
        session.add(cred1)
        session.add(contr1)
        session.commit()
        # cred1 = sqe.insert(md) # FIXME Doesn't work yet.
        # md.create_all(conn.engine)
        print("DB sample entries added")

user = relationship("User", back_populates="addresses")

