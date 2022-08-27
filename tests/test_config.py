import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException
from investmenttracker.models.config import Config

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Config(id=1, name="load.file.filename", value="/test/path"),
                Config(id=2, name="load.sFTP.username", value="fezfezfze"),
                Config(id=3, name="load.sFTP.password", value="gre814ge81:;^m"),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        config = self.database.config_get_by_name("load.file.filename")
        self.assertEqual(
            config.id,
            1,
            "1 configuration should match when searching by name",
        )

        config = self.database.config_get_by_name("does.not.exist")
        self.assertEqual(
            config,
            None,
            "Inexistant configuration should yield None",
        )

        configs = self.database.configs_get_all()
        self.assertEqual(
            configs,
            {
                "load.file.filename": "/test/path",
                "load.sFTP.username": "fezfezfze",
                "load.sFTP.password": "gre814ge81:;^m",
            },
            "Get all config fails",
        )

    def test_validations(self):
        config = self.database.config_get_by_name("load.file.filename")

        # Test mandatory fields
        for field in ["name", "value"]:
            for value in ["", None]:
                test_name = "Config must have a " + field + " that is not "
                test_name += "empty" if value == "" else str(value)
                with self.assertRaises(ValidationException) as cm:
                    setattr(config, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    config,
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
        for field in ["name", "value"]:
            test_name = "Config " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(config, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                config,
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

    def test_attributes(self):
        config = self.database.config_get_by_name("load.file.filename")
        self.assertEqual(
            str(config),
            "Config for load.file.filename : /test/path",
            "Config string representation is wrong",
        )

        # Test setting a string value
        config = self.database.config_set("load.file.filename", "blabla")
        config = self.database.config_get_by_name("load.file.filename")
        self.assertEqual(
            str(config),
            "Config for load.file.filename : blabla",
            "Config setting is wrong",
        )

        # Test setting a boolean value
        config = self.database.config_set("extra.config", False)
        config = self.database.config_get_by_name("extra.config")
        self.assertEqual(
            config.value,
            "0",
            "Config boolean setting is wrong",
        )
