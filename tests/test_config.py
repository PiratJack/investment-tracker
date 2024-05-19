import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.base import ValidationException


class TestConfig:
    def test_gets(self, app_db):
        config = app_db.config_get_by_name("load.file.filename")
        assert config.id == 1, "1 configuration should match when searching by name"

        config = app_db.config_get_by_name("does.not.exist")
        assert config is None, "Inexistant configuration should yield None"

        configs = app_db.configs_get_all()
        assert configs == {
            "load.file.filename": "/test/path",
            "load.sFTP.username": "fezfezfze",
            "load.sFTP.password": "gre814ge81:;^m",
        }, "Get all config fails"

        config = app_db.config_get_by_name("load.file.filename")
        assert (
            str(config) == "Config for load.file.filename : /test/path"
        ), "Config string representation is wrong"

        # Test setting a string value
        config = app_db.config_set("load.file.filename", "blabla")
        config = app_db.config_get_by_name("load.file.filename")
        assert (
            str(config) == "Config for load.file.filename : blabla"
        ), "Config setting is wrong"

        # Test setting a boolean value
        config = app_db.config_set("extra.config", False)
        config = app_db.config_get_by_name("extra.config")
        assert config.value == "0", "Config boolean setting is wrong"

    def test_validations(self, app_db):
        # Test mandatory fields
        item = app_db.config_get_by_name("load.file.filename")
        for field in ["name", "value"]:
            for value in ["", None]:
                test_name = "Config must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(item, field, value)
                assert cm.value.item == item, test_name + " - item is wrong"
                assert cm.value.key == field, test_name + " - key is wrong"
                assert cm.value.invalid_value == value, (
                    test_name + " - invalid_value is wrong"
                )

        # Test max length of fields
        item = app_db.config_get_by_name("load.file.filename")
        for field in ["name", "value"]:
            test_name = "Config " + field + " can't be more than 250 characters"
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
