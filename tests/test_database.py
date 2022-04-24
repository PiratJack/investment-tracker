import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel
import sqlalchemy.orm

from investmenttracker.models.account import Account
from investmenttracker.models.share import Share
from investmenttracker.models.transaction import Transaction

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Share(id=1, name="AXA", main_code="FR847238", base_currency="EUR"),
                Share(
                    id=2, name="Accenture", main_code="NYSE:ACN", base_currency="USD"
                ),
                Account(
                    id=1,
                    name="Main account",
                    code="AUFE1",
                    base_currency="EUR",
                    enabled=True,
                ),
                Transaction(
                    account_id=1,
                    date=datetime.datetime(2020, 1, 1),
                    label="First investment",
                    type="cash_entry",
                    quantity=10000,
                    unit_price=1,
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        self.assertEqual(
            len(self.database.accounts_get_all()),
            1,
            "There should be 1 account in total",
        )
        self.assertEqual(
            type(self.database.accounts_get_by_id(1)),
            Account,
            "There should be 1 account with ID 1",
        )
        self.assertRaises(
            sqlalchemy.orm.exc.NoResultFound,
            lambda _: self.database.accounts_get_by_id(2),
            "There should be no account with ID 0",
        )
        self.assertEqual(
            len(self.database.shares_get_all()), 2, "There should be 2 shares"
        )
        self.assertEqual(
            self.database.share_get_by_id(1).name, "AXA", "Share 1 should be AXA"
        )
