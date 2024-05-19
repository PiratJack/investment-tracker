import os
import sys
import datetime
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException, format_number
from models.transaction import Transaction, TransactionTypes


class TestTransaction:
    def test_gets(self, app_db):
        # Direct select
        transaction = app_db.transaction_get_by_id(1)
        assert (
            transaction.label == "First investment"
        ), "Transaction has the wrong label"

        # Select through account
        account = app_db.account_get_by_id(1)
        assert len(account.transactions) == 5, "Account has 5 transactions"

        assert (
            account.transactions[0].account == account
        ), "Transaction from account must be linked to that account"

        # String representation
        assert (
            str(account.transactions[0])
            == "Transaction ('Cash deposit', '2020-01-01', '', 'Main account')"
        ), "Transaction representation is wrong"
        assert (
            str(account.transactions[1])
            == "Transaction ('Asset buy / subscription', '2020-01-05', 'Accenture', 'Main account')"
        ), "Transaction representation is wrong"

        # Cash and Asset totals
        assert (
            account.transactions[1].cash_total == -5000
        ), "Transaction cash total is wrong"
        assert (
            account.transactions[1].asset_total == 50
        ), "Transaction asset total is wrong"

        transaction = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="asset_sell",
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        assert transaction.cash_total == 10, "Transaction cash total is wrong"
        assert transaction.asset_total == -10, "Transaction asset total is wrong"

        transaction = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="asset_sell",
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        assert (
            str(transaction)
            == "Transaction ('Asset sell', '2020-04-15 00:00:00', '', '')"
        ), "Transaction representation is wrong"

        # Database selects & filters
        transactions = app_db.transactions_get_by_account_and_shares([2], {1: [3]})
        assert len(transactions) == 3, "Complex filter should yield 3 transactions"

        # Formatting numbers
        assert format_number(0) == "-", "0 should be displayed as -"
        assert format_number(10**-9) == "-", "Small numbers should be displayed as -"
        assert (
            format_number(1584.415159) == "1584.41516"
        ), "Regular numbers should be displayed with 5 decimals"
        assert (
            format_number(1584.415159, "EUR") == "1584.42 EUR"
        ), "Currency-related numbers should be displayed with 2 decimals"

    def test_validations(self, app_db):
        # Test forbidden values
        item = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type="dividends",
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        forbidden_values = {
            "type": ["", None, 0, -1, "hfeozhfze"],
            "account_id": ["", None, 0],
            "quantity": ["", None, 0],
            "unit_price": ["", None],
            "share_id": [-1, 0],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Transaction must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test missing share for transaction with impact_asset=True
        # (has_asset=True is tested above)
        item = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
            type=TransactionTypes["asset_buy"],
            share_id=2,
            quantity=10,
            unit_price=1,
        )
        forbidden_values = {
            "share_id": [-1, 0],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Transaction must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test max length of fields
        for field in ["label"]:
            test_name = "Transaction " + field + " can't be more than 250 characters"
            value = "a" * 251
            with pytest.raises(ValidationException) as cm:
                setattr(item, field, value)
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )

        # Test transaction while it's being created (some missing fields)
        item = Transaction(
            account_id=1,
            date=datetime.datetime(2020, 4, 15),
            label="Sell ACN",
        )
        item.unit_price = 1

    def test_copy(self, app_db):
        transaction = app_db.transaction_get_by_id(1)
        transaction_copy = transaction.copy()
        app_db.session.add(transaction_copy)
        app_db.session.commit()
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
            assert getattr(transaction, attr) == getattr(transaction_copy, attr), (
                "Transaction copy - " + attr + " is not copied properly"
            )
        assert (
            transaction.id != transaction_copy.id
        ), "Transaction copy - ID is the same"

    def test_delete(self, app_db):
        account = app_db.account_get_by_id(1)
        assert len(account.transactions) == 5, "Account has 5 transactions"

        app_db.delete(account.transactions[0])

        assert len(account.transactions) == 4, "Account has 4 transactions left"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
