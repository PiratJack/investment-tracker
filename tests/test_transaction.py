import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.account import Account
from investmenttracker.models.share import Share
from investmenttracker.models.transaction import Transaction
from investmenttracker.models.base import ValidationException
from sqlalchemy.exc import StatementError

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestTransaction(unittest.TestCase):
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

    def test_validations(self):
        transaction = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="asset_sell",
            share_id=2,
            quantity=10,
            unit_price=1,
        )

        with self.assertRaises(ValidationException) as cm:
            transaction.type = "hfeozhfze"
        self.assertEquals(
            type(cm.exception),
            ValidationException,
            "Transaction must have a valid type",
        )

        mandatory_attributes = ["type", "account", "quantity", "unit_price"]
        for attribute in mandatory_attributes:
            with self.assertRaises(ValidationException) as cm:
                setattr(transaction, attribute, "")
            self.assertEquals(
                type(cm.exception),
                ValidationException,
                "Transaction must have " + attribute,
            )

            with self.assertRaises(ValidationException) as cm:
                setattr(transaction, attribute, None)
            self.assertEquals(
                type(cm.exception),
                ValidationException,
                "Transaction must have " + attribute,
            )
