import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.account import Account
from investmenttracker.models.share import Share
from investmenttracker.models.transaction import Transaction

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestAccount(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Share(id=1, name="AXA", main_code="FR847238", base_currency="EUR"),
                Share(
                    id=2, name="Accenture", main_code="NYSE:ACN", base_currency="USD"
                ),
                Share(
                    id=3, name="Workday", main_code="NASDAQ:WDAY", base_currency="USD"
                ),
                Share(id=4, name="HSBC", main_code="LU4325", base_currency="EUR"),
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
                Transaction(
                    account_id=1,
                    date=datetime.datetime(2020, 1, 5),
                    label="Buy ACN",
                    type="asset_buy",
                    share_id=2,
                    quantity=50,
                    unit_price=100,
                ),
                Transaction(
                    account_id=1,
                    date=datetime.datetime(2020, 1, 25),
                    label="Buy Workday",
                    type="asset_buy",
                    share_id=3,
                    quantity=10,
                    unit_price=200,
                ),
                Transaction(
                    account_id=1,
                    date=datetime.datetime(2020, 4, 15),
                    label="Sell ACN",
                    type="asset_sell",
                    share_id=2,
                    quantity=10,
                    unit_price=1,
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_balance(self):
        self.assertEqual(
            self.database.accounts_get_all()[0].balance,
            3010,
            "Account balance should be 3010",
        )

    def test_share_ownership(self):
        shares = self.database.accounts_get_all()[0].shares
        self.assertEqual(shares[2], 40, "Account should have 40 NYSE:ACN")
        self.assertEqual(shares[3], 10, "Account should have 10 NASDAQ:WDAY")

    def test_total_invested(self):
        total_invested = self.database.accounts_get_all()[0].total_invested
        self.assertEqual(
            total_invested, 10000, "Total invested in account should be 10k"
        )
