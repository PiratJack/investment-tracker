import os
import sys
import datetime
import sqlalchemy
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException
from models.shareprice import SharePrice


class TestSharePrice:
    def test_gets(self, app_db):
        # Get from direct query (based on date)
        share_prices = app_db.share_price_query()
        share_prices = share_prices.filter(SharePrice.date >= datetime.date(2022, 3, 1))
        assert len(share_prices.all()) == 5, "5 prices after March 1st, 2022"

        # Get from direct query (based on share)
        share_prices = app_db.share_prices_get(share_id=3)
        assert len(share_prices) == 1, "1 price for Workday"

        # Get from direct query (based on share + date)
        share_prices = app_db.share_prices_get(
            share_id=2,
            start_date=datetime.datetime(2020, 3, 1),
            end_date=datetime.datetime(2999, 1, 1),
        )
        assert len(share_prices) == 3, "3 prices for ACN after March 1st, 2020"

        # Get from share
        share = app_db.share_get_by_id(2)
        share_prices = share.prices
        assert len(share_prices) == 4, "4 prices for ACN"

        # Get from complex query
        dates = {
            datetime.datetime(2020, 1, 12): 1,
            datetime.datetime(2021, 12, 15): 0,
            datetime.datetime(2022, 4, 5): 0,
        }
        for date, nb_prices in dates.items():
            share_prices = app_db.share_prices_get(
                share_id=2, currency_id=5, start_date=date
            )
            assert len(share_prices) == nb_prices, (
                str(nb_prices) + " price for ACN in EUR 14 days prior to " + str(date)
            )

        dates = {
            datetime.datetime(2020, 1, 12): 0,
            datetime.datetime(2020, 4, 15): 1,
        }
        for date, nb_prices in dates.items():
            share_prices = app_db.share_prices_get(
                share_id=2, currency_id=5, start_date=date, exact_date=True
            )
            assert len(share_prices) == nb_prices, (
                str(nb_prices) + " price for ACN in EUR on " + str(date)
            )

        share_prices = app_db.share_prices_get(share_id=2, currency_id=5)
        assert len(share_prices) == 3, "3 price for ACN in EUR (no date filter)"
        share_prices = app_db.share_prices_get(share_id=2, currency_id=6)
        assert len(share_prices) == 1, "1 price for ACN in USD (no date filter)"

        usd_currency = app_db.share_get_by_id(6)
        share_prices = app_db.share_prices_get(share_id=2, currency_id=usd_currency)
        assert len(share_prices) == 1, "1 price for ACN in USD (no date filter)"

        accenture_share = app_db.share_get_by_id(2)
        share_prices = app_db.share_prices_get(
            share_id=accenture_share, currency_id=usd_currency
        )
        assert len(share_prices) == 1, "1 price for ACN in USD (no date filter)"

        # String representation
        share_price = app_db.share_price_get_by_id(1)
        assert (
            str(share_price) == "Price (Accenture at 100.0 EUR on 2020-01-05)"
        ), "Share price representation is wrong"
        assert (
            share_price.short_name == "100.0 EUR on 2020-01-05"
        ), "Share price short name is wrong"

        share_price = SharePrice(
            share_id=1,
            date=datetime.datetime(2022, 4, 1),
            currency_id=6,
            source="Second test",
        )
        assert (
            str(share_price) == "Price (Unknown on 2022-04-01 00:00:00)"
        ), "Share price representation is wrong"
        assert (
            share_price.short_name == "Unknown on 2022-04-01 00:00:00"
        ), "Share price short name is wrong"

        share_price = SharePrice(
            share_id=1,
            price=125,
            source="Second test",
        )
        assert (
            str(share_price) == "Price (Unknown)"
        ), "Share price representation is wrong"
        assert share_price.short_name == "Unknown", "Share price short name is wrong"

    def test_validations(self, app_db):
        item = SharePrice(
            share_id=1,
            date=datetime.datetime(2022, 4, 1),
            price=125.24,
            currency_id=5,
            source="Test suite",
        )

        # Test mandatory fields
        for field in ["share_id", "date", "price", "currency_id", "source"]:
            for value in ["", None]:
                test_name = "Share price must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test share price source max length
        test_name = "Share price can't have a source with more than 250 characters"
        field = "source"
        value = "a" * 251
        with pytest.raises(ValidationException) as cm:
            setattr(item, field, value)
        assert cm.value.item == item, test_name + " - item is wrong"
        assert cm.value.key == field, test_name + " - key is wrong"
        assert cm.value.invalid_value == value, test_name + " - invalid_value is wrong"

        # Can't have the share itself as base currency (modification of currency)
        test_name = "Share Price currency can't be the share itself"
        item = app_db.share_get_by_id(2).prices[0]
        field = "currency_id"
        value = item.share.id
        with pytest.raises(ValidationException) as cm:
            setattr(item, field, value)
        assert cm.value.item == item, test_name + " - item is wrong"
        assert cm.value.key == field, test_name + " - key is wrong"
        assert cm.value.invalid_value == value, test_name + " - invalid_value is wrong"

        # Can't have the share itself as base currency (modification of share)
        test_name = "Share Price currency can't be the share itself"
        item = app_db.share_get_by_id(2).prices[0]
        field = "share_id"
        value = item.currency.id
        with pytest.raises(ValidationException) as cm:
            setattr(item, field, value)
        assert cm.value.item == item, test_name + " - item is wrong"
        assert cm.value.key == field, test_name + " - key is wrong"
        assert cm.value.invalid_value == value, test_name + " - invalid_value is wrong"

    def test_delete(self, app_db):
        # Get from direct query (based on date)
        share_prices = app_db.share_price_query()
        share_prices = share_prices.filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        ).all()

        nb_before_delete = len(share_prices)

        app_db.delete(share_prices[0])
        share_prices = app_db.share_price_query()
        share_prices = share_prices.filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        ).all()

        assert len(share_prices) == nb_before_delete - 1, "Price deletion failed"

        # Delete price - check it's indeed deleted
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            app_db.share_price_get_by_id(3)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
