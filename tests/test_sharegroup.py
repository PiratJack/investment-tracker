import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException
from investmenttracker.models.share import Share
from investmenttracker.models.sharegroup import ShareGroup

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestShareGroup(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                ShareGroup(id=1, name="AMEX"),
                ShareGroup(id=2, name="EUREX"),
                ShareGroup(id=3, name="CURRENCY"),
                Share(
                    id=1,
                    name="AXA",
                    main_code="FR847238",
                    base_currency="EUR",
                    group_id=2,
                ),
                Share(
                    id=2,
                    name="Accenture",
                    main_code="NYSE:ACN",
                    base_currency="USD",
                    group_id=1,
                ),
                Share(
                    id=3,
                    name="Workday",
                    main_code="NYSE:WDAY",
                    base_currency="USD",
                    group_id=1,
                ),
                Share(
                    id=4, name="USD", main_code="USD", base_currency="USD", group_id=3
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        share_group = self.database.share_group_get_by_id(1)
        self.assertEqual(
            len(share_group.shares),
            2,
            "AMEX group has 2 shares",
        )

    def test_validations(self):
        share_group = self.database.share_group_get_by_id(1)

        # Test mandatory fields
        for field in ["name"]:
            for value in ["", None]:
                test_name = "Share price must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(share_group, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    share_group,
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
        for field in ["name"]:
            test_name = "Account " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(share_group, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                share_group,
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
