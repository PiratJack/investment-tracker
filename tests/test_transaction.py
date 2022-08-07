import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException, format_number
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
                Share(id=1, name="AXA", main_code="FR847238", base_currency_id=5),
                Share(id=2, name="Accenture", main_code="NYSE:ACN", base_currency_id=6),
                Share(id=3, name="Workday", main_code="WDAY", base_currency_id=6),
                Share(id=4, name="HSBC", main_code="LU4325", base_currency_id=5),
                Share(id=5, name="Euro", main_code="EUR"),
                Share(id=6, name="Dollar", main_code="USD"),
                Account(
                    id=1,
                    name="Main account",
                    code="AUFE1",
                    base_currency_id=5,
                    enabled=True,
                ),
                Account(
                    id=2,
                    name="Secondary account",
                    code="htrthr",
                    base_currency_id=5,
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
                Transaction(
                    account_id=2,
                    date=datetime.datetime(2020, 4, 15),
                    label="First investment",
                    type="cash_entry",
                    quantity=2500,
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
        # Direct select
        transaction = self.database.transaction_get_by_id(1)
        self.assertEqual(
            transaction.label,
            "First investment",
            "Transaction has the wrong label",
        )

        # Select through account
        account = self.database.account_get_by_id(1)
        self.assertEqual(
            len(account.transactions),
            4,
            "Account has 4 transactions",
        )

        self.assertEqual(
            account.transactions[0].account,
            account,
            "Transaction from account must be linked to that account",
        )

        # String representation
        self.assertEqual(
            str(account.transactions[0]),
            "Transaction ('Cash deposit', '2020-01-01', '', 'Main account')",
            "Transaction representation is wrong",
        )
        self.assertEqual(
            str(account.transactions[1]),
            "Transaction ('Asset buy / subscription', '2020-01-05', 'Accenture', 'Main account')",
            "Transaction representation is wrong",
        )

        # Cash and Asset totals
        self.assertEqual(
            account.transactions[1].cash_total,
            -5000,
            "Transaction cash total is wrong",
        )
        self.assertEqual(
            account.transactions[1].asset_total,
            50,
            "Transaction asset total is wrong",
        )

        transaction = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="asset_sell",
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        self.assertEqual(
            transaction.cash_total,
            10,
            "Transaction cash total is wrong",
        )
        self.assertEqual(
            transaction.asset_total,
            -10,
            "Transaction asset total is wrong",
        )

        transaction = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="asset_sell",
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        self.assertEqual(
            str(transaction),
            "Transaction ('asset_sell', '2020-04-15 00:00:00', '', '')",
            "Transaction representation is wrong",
        )

        # Database selects & filters
        transactions = self.database.transactions_get_by_account_and_shares(
            [2], {1: [3]}
        )
        self.assertEqual(
            len(transactions),
            2,
            "Complex filter should yield 2 transactions",
        )

        # Formatting numbers
        self.assertEqual(
            format_number(0),
            "-",
            "0 should be displayed as -",
        )
        self.assertEqual(
            format_number(10**-9),
            "-",
            "Small numbers should be displayed as -",
        )
        self.assertEqual(
            format_number(1584.415159),
            "1584.42",
            "Regular numbers should be displayed with 2 decimals",
        )
        self.assertEqual(
            format_number(1584.415159, "EUR"),
            "1584.42 EUR",
            "Regular numbers should be displayed with 2 decimals",
        )

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

        # Test forbidden values
        forbidden_values = {
            "type": ["", None, 0, -1],
            "account_id": ["", None, 0],
            "quantity": ["", None, 0],
            "unit_price": ["", None],
            "share_id": [-1, 0],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Transaction must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(transaction, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    transaction,
                    test_name + " - exception.item is wrong",
                )
                self.assertEqual(
                    cm.exception.key,
                    field,
                    test_name + " - exception.key is wrong",
                )
                self.assertEqual(
                    cm.exception.invalid_value,
                    value,
                    test_name + " - exception.invalid_value is wrong",
                )

        # Test max length of fields
        for field in ["label"]:
            test_name = "Transaction " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(transaction, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                transaction,
                test_name + " - exception.item is wrong",
            )
            self.assertEqual(
                cm.exception.key,
                field,
                test_name + " - exception.key is wrong",
            )
            self.assertEqual(
                cm.exception.invalid_value,
                value,
                test_name + " - exception.invalid_value is wrong",
            )

    def test_copy(self):
        transaction = self.database.transaction_get_by_id(1)
        transaction_copy = transaction.copy()
        self.database.session.add(transaction_copy)
        self.database.session.commit()
        for attr in [
            "date",
            "label",
            "type",
            "quantity",
            "unit_price",
            "share_id",
            "account_id",
            "share",
            "account",
        ]:
            self.assertEqual(
                getattr(transaction, attr),
                getattr(transaction_copy, attr),
                "Transaction copy - " + attr + " is not copied properly",
            )
        self.assertNotEqual(
            transaction.id,
            transaction_copy.id,
            "Transaction copy - ID is the same",
        )

    def test_delete(self):
        account = self.database.account_get_by_id(1)
        self.assertEqual(
            len(account.transactions),
            4,
            "Account has 4 transactions",
        )

        self.database.transaction_delete(account.transactions[0])

        self.assertEqual(
            len(account.transactions), 3, "Account has 3 transactions after deletion"
        )
