import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel
from sqlalchemy.orm.exc import NoResultFound

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


class TestAccount(unittest.TestCase):
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
                    name="Hidden account",
                    code="487485",
                    base_currency_id=5,
                    hidden=True,
                ),
                Account(
                    id=3,
                    name="Disabled account",
                    code="54614",
                    base_currency_id=5,
                    enabled=False,
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

    def test_gets(self):
        # Database selects & filters
        self.assertRaises(
            NoResultFound,
            lambda _: self.database.accounts_get_by_id(0),
            "There should be no account with ID 0",
        )
        self.assertEqual(
            type(self.database.accounts_get_by_id(1)),
            Account,
            "There should be 1 account with ID 1",
        )
        self.assertEqual(
            len(self.database.accounts_get_all()),
            1,
            "Only 1 account is visible & enabled",
        )
        self.assertEqual(
            len(self.database.accounts_get(with_hidden=True)),
            2,
            "There are 2 hidden or visible accounts",
        )
        self.assertEqual(
            len(self.database.accounts_get(with_disabled=True)),
            2,
            "There are 2 non-hidden accounts",
        )
        self.assertEqual(
            len(self.database.accounts_get(with_disabled=True, with_hidden=True)),
            3,
            "There are 3 accounts in total",
        )

        # Base currency
        account = self.database.accounts_get_by_id(1)
        account.base_currency = self.database.share_get_by_id(6)
        self.assertEqual(
            account.base_currency.main_code,
            "USD",
            "Account has EUR as base currency",
        )

        # String representation
        account = self.database.accounts_get_by_id(1)
        self.assertEqual(
            str(account),
            "Account Main account (AUFE1, enabled, visible)",
            "Account representation is wrong",
        )
        account = Account(
            id=2,
            name="Hidden account",
            code="487485",
            base_currency_id=5,
            hidden=True,
        )
        self.assertEqual(
            str(account),
            "Account Hidden account (487485, enabled, hidden)",
            "Account representation is wrong",
        )

    def test_attributes(self):
        # Account balance
        self.assertEqual(
            self.database.accounts_get_all()[0].balance,
            3010,
            "Account balance should be 3010",
        )

        # Shares held
        shares = self.database.accounts_get_all()[0].shares
        self.assertEqual(shares[2], 40, "Account should have 40 NYSE:ACN")
        self.assertEqual(shares[3], 10, "Account should have 10 NASDAQ:WDAY")

        # Total invested
        total_invested = self.database.accounts_get_all()[0].total_invested
        self.assertEqual(
            total_invested, 10000, "Total invested in account should be 10k"
        )

        # Total value
        total_value = self.database.accounts_get_all()[0].total_value
        self.assertEqual(total_value, 0, "INVALID TEST")

    def test_validations(self):
        account = Account(
            id=50,
            name="test",
            code="Error",
            base_currency_id=5,
            enabled=True,
        )

        # Test mandatory fields
        for field in ["name", "base_currency"]:
            for value in ["", None]:
                test_name = "Account must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(account, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    account,
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
        for field in ["name", "code"]:
            test_name = "Account " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(account, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                account,
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
