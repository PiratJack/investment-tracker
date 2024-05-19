import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException


class TestShareCode:
    def test_gets(self, app_db):
        share = app_db.share_get_by_id(1)
        share_code = share.codes[0]
        assert len(share.codes) == 3, "ACN share has 3 codes"
        assert (
            str(share_code) == "ShareCode AXA (1rACN @ Boursorama)"
        ), "ShareCode representation is wrong"

        # Search shares by various fields
        share = app_db.share_search("AXA")
        assert len(share) == 1, "Only 1 by searching 'AXA' (via name)"
        assert share[0].id == 1, "Only 1 by searching 'AXA' (via name)"

        share = app_db.share_search("FR8472")
        assert len(share) == 1, "Only 1 by searching 'FR8472' (via main code)"
        assert share[0].id == 1, "Only 1 by searching 'FR8472' (via main code)"

        share = app_db.share_search("FR4941")
        assert len(share) == 1, "Only 1 by searching 'FR4941' (via code)"
        assert share[0].id == 1, "Only 1 by searching 'FR4941' (via code)"

        # Check search returns a single share, even if it matches through different means
        share = app_db.share_search("NYSE:ACN")
        assert len(share) == 1, "Only 1 by searching 'NYSE:ACN' (no duplicate)"

        # Check search returns a single share based on ID
        share = app_db.share_search(2)
        assert len(share) == 1, "Only 1 by searching 2 (via id)"

    def test_validations(self, app_db):

        # Test forbidden values
        forbidden_values = {
            "value": ["", None],
            "origin": ["", None, -1, "uohih"],
            "share_id": ["", None, 0],
        }
        item = app_db.share_get_by_id(1).codes[0]
        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Share code must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test max length of fields
        item = app_db.share_get_by_id(1).codes[0]
        for field in ["value"]:
            test_name = "Share code " + field + " can't be more than 250 characters"
            value = "a" * 251
            with pytest.raises(ValidationException) as cm:
                setattr(item, field, value)
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )

        # Test share code origin with int values
        item = app_db.share_get_by_id(1).codes[0]
        for field in ["share_id", "origin", "value"]:
            for value in ["", None]:
                test_name = "Share code must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
