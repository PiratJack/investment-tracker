import os
import sys
import pytest
import datetime
import logging

pytest.BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(pytest.BASE_DIR, "investmenttracker"))

import controllers.mainwindow

from models.database import Database
from models.pluginmanager import PluginManager

from models.account import Account
from models.share import Share, ShareDataOrigin
from models.sharecode import ShareCode
from models.sharegroup import ShareGroup
from models.transaction import Transaction
from models.shareprice import SharePrice
from models.config import Config


def pytest_configure():
    pytest.BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(os.path.join(pytest.BASE_DIR, "investmenttracker"))
    pytest.DATABASE_FILE = ":memory:"

    logging.basicConfig(level=logging.CRITICAL)

    pytest.PLUGIN_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "investmenttracker", "plugins"
    )

    # Date for a recent share price
    # It must be in the current month and less than 15 days ago
    five_days_ago = datetime.date.today() + datetime.timedelta(days=-5)
    first_this_month = datetime.date.today().replace(day=1)
    pytest.SOME_DAYS_AGO = max(five_days_ago, first_this_month)


@pytest.fixture
def app_pluginmanager():
    pluginmanager = PluginManager(pytest.PLUGIN_FOLDER)
    yield pluginmanager


@pytest.fixture
def app_empty_db(app_pluginmanager):
    database = Database(pytest.DATABASE_FILE, app_pluginmanager)

    yield database


@pytest.fixture
def app_db(app_empty_db, monkeypatch):
    app_empty_db.session.add_all(
        [
            ShareGroup(id=1, name="AMEX"),
            ShareGroup(id=2, name="EUREX"),
            ShareGroup(id=3, name="CURRENCY"),
            Share(id=1, name="AXA", main_code="FR8472", base_currency_id=5, group_id=2),
            Share(
                id=2,
                name="Accenture",
                main_code="NYSE:ACN",
                base_currency_id=6,
                group_id=1,
                sync_origin=None,
            ),
            Share(
                id=3,
                name="Workday",
                main_code="WDAY",
                base_currency_id=6,
                group_id=1,
                sync_origin=ShareDataOrigin["alphavantage"],
            ),
            Share(
                id=4, name="HSBC", main_code="LU4325", base_currency_id=5, hidden=True
            ),
            Share(id=5, name="Euro", main_code="EUR"),
            Share(id=6, name="Dollar", main_code="USD", group_id=3),
            Share(
                id=7,
                name="BNP",
                main_code="FR:BNP",
                base_currency_id=5,
                hidden=True,
                group_id=2,
            ),
            ShareCode(share_id=1, origin="boursorama", value="1rACN"),
            ShareCode(share_id=1, origin="quantalys", value="14587"),
            ShareCode(share_id=1, origin="alphavantage", value="FR4941"),
            ShareCode(share_id=2, origin="quantalys", value="478924"),
            ShareCode(
                share_id=2, origin=ShareDataOrigin["alphavantage"], value="NYSE:ACN"
            ),
            ShareCode(share_id=3, origin="alphavantage", value="1rWDAY"),
            Account(  # Account 1 "Main account"
                id=1,
                name="Main account",
                code="AUFE1",
                base_currency_id=5,
                enabled=True,
            ),
            Account(  # Account 2 "Hidden account"
                id=2,
                name="Hidden account",
                code="487485",
                base_currency_id=5,
                hidden=True,
            ),
            Account(  # Account 3 "Disabled account"
                id=3,
                name="Disabled account",
                code="54614",
                base_currency_id=5,
                enabled=False,
            ),
            Account(  # Account 4 "Account with lots of history"
                id=4,
                name="Account with lots of history",
                code="HIST",
                base_currency_id=5,
                enabled=True,
            ),
            Account(  # Account 5 "Account with no history"
                id=5,
                name="Account with no history",
                code="HIST",
                base_currency_id=5,
            ),
            Account(  # Account 6 "Test account in EUR"
                id=6,
                name="Test account in EUR",
                code="TEST",
                base_currency_id=5,
            ),
            Transaction(  # Account 1: deposit 10k on January 1st, 2020
                account_id=1,
                date=datetime.date(2020, 1, 1),
                label="First investment",
                type="cash_entry",
                quantity=10000,
                unit_price=1,
            ),
            Transaction(  # Account 1: buy 50 ACN at 100 on January 5th, 2020
                account_id=1,
                date=datetime.date(2020, 1, 5),
                label="Buy ACN",
                type="asset_buy",
                share_id=2,
                quantity=50,
                unit_price=100,
            ),
            Transaction(  # Account 1: buy 10 WDAY at 200 on January 25th, 2020
                account_id=1,
                date=datetime.date(2020, 1, 25),
                label="Buy Workday",
                type="asset_buy",
                share_id=3,
                quantity=10,
                unit_price=200,
            ),
            Transaction(  # Account 1: sell 10 ACN at 1 on April 15th, 2020
                account_id=1,
                date=datetime.date(2020, 4, 15),
                label="Sell ACN",
                type="asset_sell",
                share_id=2,
                quantity=10,
                unit_price=1,
            ),
            Transaction(  # Account 1: company funding of 100 EUR on April 15th 2020
                account_id=1,
                date=datetime.date(2020, 4, 15),
                label="Get funded",
                type="company_funding_cash",
                share_id=5,
                quantity=100,
                unit_price=1,
            ),
            Transaction(  # Account 2: Cash entry of 10 k
                account_id=2,
                date=datetime.date(2021, 1, 1),
                label="Invest 10 k",
                type="cash_entry",
                quantity=10000,
                unit_price=1,
            ),
            Transaction(  # Account 2: Cash exit of 10 k
                account_id=2,
                date=datetime.date(2022, 1, 1),
                label="Withdraw 10 k",
                type="cash_exit",
                quantity=10000,
                unit_price=1,
            ),
            Transaction(  # Account 3: Cash entry of 10
                account_id=3,
                date=datetime.date(2020, 1, 10),
                label="Deposit 10",
                type="cash_entry",
                quantity=10,
                unit_price=1,
            ),
            Transaction(  # Account 3: buy 10 EUR with EUR (absurd, just for test)
                account_id=3,
                date=datetime.date(2020, 4, 10),
                label="Buy EUR",
                type="asset_buy",
                share_id=5,
                quantity=10,
                unit_price=1,
            ),
            Transaction(  # Account 4: deposit 10k on April 1st, 2020
                account_id=4,
                date=datetime.date(2020, 4, 1),
                label="First investment",
                type="cash_entry",
                quantity=10000,
                unit_price=1,
            ),
            Transaction(  # Account 4: buy 10 ACN at 200 on April 1th, 2020
                account_id=4,
                date=datetime.date(2020, 4, 1),
                label="Buy Accenture",
                type="asset_buy",
                share_id=2,
                quantity=10,
                unit_price=200,
            ),
            Transaction(  # Account 4: buy 30 HSBC at 100 on April 1th, 2020
                account_id=4,
                date=datetime.date(2020, 4, 1),
                label="Buy HSBC",
                type="asset_buy",
                share_id=4,
                quantity=30,
                unit_price=100,
            ),
            Transaction(  # Account 4: sell 5 ACN at 250 on April 10th, 2020
                account_id=4,
                date=datetime.date(2020, 4, 10),
                label="Sell Accenture",
                type="asset_sell",
                share_id=2,
                quantity=5,
                unit_price=250,
            ),
            Transaction(  # Account 4: buy 20 HSBC at 125 on April 10th, 2020
                account_id=4,
                date=datetime.date(2020, 4, 10),
                label="Buy HSBC again",
                type="asset_buy",
                share_id=4,
                quantity=20,
                unit_price=125,
            ),
            Transaction(  # Account 6: Cash entry of 10k on October 1st, 2023
                account_id=6,
                date=datetime.date(2023, 10, 1),
                label="Cash entry",
                type="cash_entry",
                quantity=10000,
                unit_price=1,
            ),
            Transaction(  # Account 6: buy 100 BNP at 50 on Nov 1st, 2023
                account_id=6,
                date=datetime.date(2023, 11, 1),
                label="Buy BNP",
                type="asset_buy",
                share_id=7,
                quantity=100,
                unit_price=50,
            ),
            Transaction(  # Account 6: remove 1000 EUR 4 months ago on 5th of month
                account_id=6,
                date=(datetime.date.today() + datetime.timedelta(days=-4 * 30)).replace(
                    day=5
                ),
                label="Withdraw cash",
                type="cash_exit",
                quantity=1000,
                unit_price=1,
            ),
            SharePrice(  # ACN at 100 EUR on January 5th, 2020
                share_id=2,
                date=datetime.date(2020, 1, 5),
                price=100,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # ACN at 1 EUR on April 15th, 2020
                share_id=2,
                date=datetime.date(2020, 4, 15),
                price=1,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # ACN at 10 EUR at a recent date
                share_id=2,
                date=pytest.SOME_DAYS_AGO,
                price=10,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # ACN at 12 USD on April 15th, 2023
                share_id=2,
                date=datetime.date(2023, 4, 15),
                price=12,
                currency_id=6,
                source="Lambda",
            ),
            SharePrice(  # WDAY at 10 USD at a recent date
                share_id=3,
                date=pytest.SOME_DAYS_AGO,
                price=10,
                currency_id=6,
                source="Lambda",
            ),
            SharePrice(  # USD at 10 EUR at a recent date
                share_id=6,
                date=pytest.SOME_DAYS_AGO,
                price=10,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # HSBC at 10 AXA at a recent date (which makes no sense)
                share_id=4,
                date=pytest.SOME_DAYS_AGO,
                price=10,
                currency_id=1,
                source="Lambda",
            ),
            SharePrice(  # BNP at 50 EUR on Nov 1st, 2023 (when it was bought)
                share_id=7,
                date=datetime.date(2023, 11, 1),
                price=50,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 50 EUR 7 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-7 * 30)).replace(
                    day=1
                ),
                price=50,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 55 EUR 6 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-6 * 30)).replace(
                    day=1
                ),
                price=55,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 52 EUR 5 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-5 * 30)).replace(
                    day=1
                ),
                price=52,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 53 EUR 4 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-4 * 30)).replace(
                    day=1
                ),
                price=53,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 58 EUR 3 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-3 * 30)).replace(
                    day=1
                ),
                price=58,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 60 EUR 2 months ago
                share_id=7,
                date=(datetime.date.today() + datetime.timedelta(days=-2 * 30)).replace(
                    day=1
                ),
                price=60,
                currency_id=5,
                source="Lambda",
            ),
            SharePrice(  # BNP at 57 EUR at a recent date
                share_id=7,
                date=pytest.SOME_DAYS_AGO,
                price=57,
                currency_id=5,
                source="Lambda",
            ),
            Config(id=1, name="load.file.filename", value="/test/path"),
            Config(id=2, name="load.sFTP.username", value="fezfezfze"),
            Config(id=3, name="load.sFTP.password", value="gre814ge81:;^m"),
        ]
    )
    app_empty_db.session.commit()

    yield app_empty_db

    app_empty_db.session.close()
    app_empty_db.engine.dispose()


@pytest.fixture
# qtbot is here to make sure we have a QApplication running
def app_mainwindow(qtbot, app_db, app_pluginmanager):
    mainwindow = controllers.mainwindow.MainWindow(app_db, app_pluginmanager)

    yield mainwindow

    mainwindow.database.session.close()
    mainwindow.database.engine.dispose()
