import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException, NoPriceException
from models.share import Share


class TestShare:
    def test_gets(self, app_db):
        # Database selects & filters
        assert len(app_db.shares_query().all()) == 6, "6 shares in total"
        assert len(app_db.shares_get()) == 5, "5 shares are visible"
        assert len(app_db.shares_get(with_hidden=True)) == 6, "6 shares in total"
        assert len(app_db.shares_get(only_synced=True)) == 1, "1 share is synced"

        # String representations
        share = app_db.share_get_by_id(1)
        assert str(share) == "Share AXA (FR8472, EUR, unsynced)", "Share str is wrong"
        assert share.short_name == "AXA (FR8472)", "Share short name is wrong"
        assert share.graph_label == "AXA (Euro)", "Share graph_label is wrong"
        share = app_db.share_get_by_id(3)
        assert str(share) == "Share Workday (WDAY, USD, synced)", "Share str is wrong"
        assert share.short_name == "Workday (WDAY)", "Share short name is wrong"
        assert share.graph_label == "Workday (Dollar)", "Share graph_label is wrong"

        # Last price
        share = app_db.share_get_by_id(1)
        test_name = "Missing last price should raise NoPriceException"
        with pytest.raises(NoPriceException) as cm:
            share.last_price
        assert cm.value.share == share, test_name + " - share is wrong"

        last_price = app_db.share_get_by_id(2).last_price
        assert last_price.price == 10, "Last price is 10 EUR"
        assert last_price.currency.main_code == "EUR", "Last price is 10 EUR"
        assert last_price.source == "Lambda", "Last price source is wrong"

        # Code for sync
        share = app_db.share_get_by_id(1)
        assert share.code_sync_origin == "", "Share code for sync origin is wrong"
        share = app_db.share_get_by_id(3)
        assert share.code_sync_origin == "1rWDAY", "Share code for sync origin is wrong"

    def test_validations(self, app_db):

        # Test mandatory fields
        item = Share(id=1, name="Test share", main_code="FE4451")
        for field in ["name"]:
            for value in ["", None]:
                test_name = "Share must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test max length of fields
        item = Share(id=1, name="Test share", main_code="FE4451")
        for field in ["name", "main_code"]:
            test_name = "Share " + field + " can't be more than 250 characters"
            value = "a" * 251
            with pytest.raises(ValidationException) as cm:
                setattr(item, field, value)
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )

        # Can't have itself as base currency
        item = app_db.share_get_by_id(5)
        test_name = "Share can't have itself as base currency"
        field = "base_currency_id"
        value = item.id
        with pytest.raises(ValidationException) as cm:
            setattr(item, field, value)
        assert cm.value.item == item, test_name + " - item is wrong"
        assert cm.value.key == field, test_name + " - key is wrong"
        assert cm.value.invalid_value == item.id, (
            test_name + " - invalid_value is wrong"
        )
        field = "base_currency"
        value = item
        with pytest.raises(ValidationException) as cm:
            setattr(item, field, value)
        assert cm.value.item == item, test_name + " - item is wrong"
        assert cm.value.key == field, test_name + " - key is wrong"
        assert cm.value.invalid_value == item, test_name + " - invalid_value is wrong"
        # Test a valid value
        field = "base_currency"
        value = app_db.share_get_by_id(1)
        setattr(item, field, value)

        # Test invalid sync_origin attribute
        item = app_db.share_get_by_id(1)
        field = "sync_origin"
        forbidden_values = ["fheozhfei", -2]
        for value in forbidden_values:
            test_name = "Share must have a valid sync_origin attribute"
            with pytest.raises(ValidationException) as cm:
                item.sync_origin = value
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
