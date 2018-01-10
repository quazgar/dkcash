"""Binding functions and classes to the GnuCash database.

Implementation notes
--------------------

Piecash requires SqlAlchemy classes to have a few special methods,
e.g. `object_to_validate`.  This probably means that content similar to
`sa_extra` module should be used, this is provided by the piecash_compat module.

"""

import os
import uuid

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
from piecash.core.account import AccountType

from .piecash_compat import DeclarativeBase as PCCDeclarativeBase

class DKDatabase:
    """Wrapper around the (modified) GnuCash database."""
    def __init__(self, filename, sample_entries=False):
        if os.path.exists(filename):
            self.book = piecash.open_book(filename,
                                          readonly=False)
        else:
            self.book = piecash.create_book(sqlite_file=filename)
        self._enrich_database()
        if sample_entries:
            self._add_sample_entries()

    def _enrich_database(self):
        """Add the necessary extra accounts and tables if necessary."""
        self._init_accounts()
        session = self.book.session
        conn = session.connection()
        md = sch.MetaData(bind=conn, reflect=True)
        Base = declarative_base(bind=conn, metadata=md)
        class Creditor(Base):
            __tablename__ = "creditors"
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

        cred1 = Creditor(
            creditor_id=str(uuid.uuid4()),
            name="Newly newt",
            address1="New Street 1",
            address2="12345 Irgendwo",
            newsletter=True
        )

        Base.metadata.create_all(conn.engine)

        print("DB enriched")

    def _init_accounts(self):
        acc = Account(name="My account",
                      type="ASSET",
                      parent=book.root_account,
                      commodity=EUR,
                      placeholder=True,)
        subacc = Account(name="My sub account",
                         type="BANK",
                         parent=acc,
                         commodity=EUR,
                         commodity_scu=1000,
                         description="my bank account",
                         code="FR013334...",)

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
        embed()
        contr1 = Contract(
            contract_id="23",
            creditor=cred1,
        )
        session.add(cred1)
        session.commit()
        embed()
        # cred1 = sqe.insert(md) # FIXME Doesn't work yet.
        # md.create_all(conn.engine)
        print("DB sample entries added")

user = relationship("User", back_populates="addresses")

