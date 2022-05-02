import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException
from investmenttracker.models.account import Account
from investmenttracker.models.share import Share
from investmenttracker.models.transaction import Transaction

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

        # Test invalid type attribute
        test_name = "Transaction must have a valid type"
        with self.assertRaises(ValidationException) as cm:
            transaction.type = "hfeozhfze"
        self.assertEqual(
            type(cm.exception),
            ValidationException,
            test_name + " - exception type is wrong",
        )
        self.assertEqual(
            cm.exception.item,
            transaction,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "type",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "hfeozhfze",
            test_name + " - exception.invalid_value is wrong",
        )

        # Test max length for transaction label
        test_name = "Transaction must have a label with less than 250 characters"
        with self.assertRaises(ValidationException) as cm:
            transaction.label = "a" * 251
        self.assertEqual(
            type(cm.exception),
            ValidationException,
            test_name + " - exception type is wrong",
        )
        self.assertEqual(
            cm.exception.item,
            transaction,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "label",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "a" * 251,
            test_name + " - exception.invalid_value is wrong",
        )

        mandatory_attributes = ["type", "account", "quantity", "unit_price"]
        for attribute in mandatory_attributes:
            # Test empty value
            test_name = "Transaction must have non-empty " + attribute
            with self.assertRaises(ValidationException) as cm:
                setattr(transaction, attribute, "")
            self.assertEqual(
                type(cm.exception),
                ValidationException,
                test_name,
            )
            self.assertEqual(
                cm.exception.item,
                transaction,
                test_name + " - exception.item is wrong",
            )
            self.assertEqual(
                cm.exception.key,
                attribute,
                test_name + " - exception.key is wrong",
            )
            self.assertEqual(
                cm.exception.invalid_value,
                "",
                test_name + " - exception.invalid_value is wrong",
            )

            # Test None value
            test_name = "Transaction must have non-None " + attribute
            with self.assertRaises(ValidationException) as cm:
                setattr(transaction, attribute, None)
            self.assertEqual(
                type(cm.exception),
                ValidationException,
                test_name,
            )

            self.assertEqual(
                cm.exception.item,
                transaction,
                test_name + " - exception.item is wrong",
            )
            self.assertEqual(
                cm.exception.key,
                attribute,
                test_name + " - exception.key is wrong",
            )
            self.assertEqual(
                cm.exception.invalid_value,
                None,
                test_name + " - exception.invalid_value is wrong",
            )
