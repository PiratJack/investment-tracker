import os
import sys
import datetime
import sqlalchemy
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import NoPriceException, ValidationException
from models.account import Account
from models.share import Share
from models.transaction import Transaction


class TestAccount:
    def test_gets(self, app_db):
        # Database selects & filters
        test_name = "There should be no account with ID 0"
        with pytest.raises(sqlalchemy.exc.NoResultFound) as cm:
            app_db.account_get_by_id(0)
        assert isinstance(
            app_db.account_get_by_id(1), Account
        ), "There should be 1 account with ID 1"
        assert len(app_db.accounts_get()) == 3, "3 accounts are visible & enabled"
        assert (
            len(app_db.accounts_get(with_hidden=True)) == 4
        ), "4 hidden or visible accounts"
        assert (
            len(app_db.accounts_get(with_disabled=True)) == 4
        ), "4 non-hidden accounts"
        assert (
            len(app_db.accounts_get(with_disabled=True, with_hidden=True)) == 5
        ), "5 accounts in total"

        # Check account attributes
        account = app_db.account_get_by_id(1)
        assert (
            account.base_currency.main_code == "EUR"
        ), "Account has EUR as base currency"
        assert (
            str(account) == "Account Main account (AUFE1, enabled, visible)"
        ), "Account str is wrong"
        assert (
            account.graph_label == "Main account (Euro)"
        ), "Account graph_label is wrong"
        assert account.start_date == datetime.date(
            2020, 1, 1
        ), "Account start_date is wrong"
        assert account.balance == 3110, "Account balance is wrong"
        assert account.total_invested == 10**4, "Account total_invested is wrong"
        assert account.total_value == 4510, "Account total_value is wrong"
        assert account.shares[2] == 40, "Account should have 40 NYSE:ACN"
        assert account.shares[3] == 10, "Account should have 10 NASDAQ:WDAY"

        ##### Holdings #####
        holdings = account.holdings
        expected_holdings = {
            datetime.date(2020, 1, 1): {"cash": 10000, "shares": {}},
            datetime.date(2020, 1, 5): {"cash": 5000, "shares": {2: 50}},
            datetime.date(2020, 1, 25): {"cash": 3000, "shares": {2: 50, 3: 10}},
            datetime.date(2020, 4, 15): {"cash": 3110, "shares": {2: 40, 3: 10}},
        }
        for test_date in expected_holdings:
            assert test_date in holdings, "Holdings date missing for " + str(test_date)
            assert (
                holdings[test_date] == expected_holdings[test_date]
            ), "Holdings wrong as of " + str(test_date)

        account = app_db.account_get_by_id(2)
        assert (
            str(account) == "Account Hidden account (487485, enabled, hidden)"
        ), "Account str is wrong"
        assert (
            account.graph_label == "Hidden account (Euro)"
        ), "Account graph_label is wrong"
        assert account.start_date == datetime.date(
            2021, 1, 1
        ), "Account start_date is wrong"
        assert account.balance == 0, "Account balance is wrong"
        assert account.total_invested == 10**4, "Account total_invested is wrong"
        assert account.total_value == 0, "Account total_value is wrong"
        assert account.shares == {}, "Account shares is wrong"
        # Account with no transaction
        account = app_db.account_get_by_id(5)
        assert account.start_date == None, "Account start_date is wrong"
        # Account with holdings = base currency
        account = app_db.account_get_by_id(3)
        assert account.total_value == 10, "Account total_value is wrong"

        # Check balance with transactions
        account = app_db.account_get_by_id(2)
        transaction = Transaction(
            account_id=2,
            date=datetime.date(2021, 4, 10),
            label="Buy shares",
            type="asset_buy",
            quantity=75,
            unit_price=10,
        )
        balance = account.balance_before_staged_transaction(transaction)
        assert balance[0] == 10**4, "Initial cash balance is wrong"
        assert balance[1] == 0, "Initial asset balance is wrong"
        app_db.session.add(transaction)
        app_db.session.commit()

        balance = account.balance_after_transaction(transaction)
        assert balance[0] == 10**4 - 750, "After transaction cash balance is wrong"
        assert balance[1] == 75, "After transaction asset balance is wrong"

        # No price exists, should raise an exception
        test_name = "No price available, should raise an exception"
        with pytest.raises(NoPriceException) as cm:
            app_db.account_get_by_id(4).total_value
        assert isinstance(cm.value.share, Share), test_name
        assert cm.value.share == app_db.share_get_by_id(4), test_name

        # Transaction doesn't exist, should raise an exception
        test_name = "This transaction doesn't exist"
        with pytest.raises(ValueError) as cm:
            account.balance_after_transaction(8257)

        # Transaction is from another account
        test_name = "This transaction is for another account"
        with pytest.raises(ValueError) as cm:
            account.balance_after_transaction(1)
        with pytest.raises(ValueError) as cm:
            account.balance_after_transaction(app_db.transaction_get_by_id(4))

    def test_validations(self, app_db):
        # Test mandatory fields
        item = Account(id=50, name="test", code="Error", enabled=True)
        for field in ["name", "base_currency"]:
            for value in ["", None]:
                test_name = "Account must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test max length of fields
        item = Account(id=50, name="test", code="Error", enabled=True)
        for field in ["name", "code"]:
            test_name = "Account " + field + " can't be more than 250 characters"
            value = "a" * 251
            with pytest.raises(ValidationException) as cm:
                setattr(item, field, value)
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )

        # Test normal values for fields
        item = Account(id=50, name="test", code="Error", enabled=True)
        item.base_currency = app_db.share_get_by_id(1)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
