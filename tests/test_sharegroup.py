import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException


class TestShareGroup:
    def test_gets(self, app_db):
        assert len(app_db.share_groups_get_all()) == 3, "There are 3 groups in total"
        share_group = app_db.share_group_get_by_id(1)
        assert len(share_group.shares) == 2, "AMEX group has 2 shares"

    def test_validations(self, app_db):
        # Test mandatory fields
        item = app_db.share_group_get_by_id(1)
        for field in ["name"]:
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

        # Test max length of fields
        item = app_db.share_group_get_by_id(1)
        for field in ["name"]:
            test_name = "Account " + field + " can't be more than 250 characters"
            value = "a" * 251
            with pytest.raises(ValidationException) as cm:
                setattr(item, field, value)
            assert cm.value.item == item, test_name + " - item is wrong"
            assert cm.value.key == field, test_name + " - key is wrong"
            assert cm.value.invalid_value == value, (
                test_name + " - invalid_value is wrong"
            )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
