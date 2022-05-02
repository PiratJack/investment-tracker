import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.share import Share
from investmenttracker.models.shareprice import SharePrice
from investmenttracker.models.base import NoPriceException
from investmenttracker.models.base import ValidationException

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestShare(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Share(id=1, name="AXA", main_code="FR847238", base_currency="EUR"),
                Share(
                    id=2, name="Accenture", main_code="NYSE:ACN", base_currency="USD"
                ),
                Share(
                    id=3,
                    name="Hidden share",
                    main_code="FEFZE",
                    base_currency="XFE",
                    hidden=True,
                ),
                SharePrice(
                    share_id=2,
                    date=datetime.datetime(2022, 1, 1),
                    price=458,
                    currency="EUR",
                    source="Test",
                ),
                SharePrice(
                    share_id=2,
                    date=datetime.datetime(2022, 4, 1),
                    price=550,
                    currency="USD",
                    source="Second test",
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_hidden(self):
        self.assertEqual(
            len(self.database.shares_get_all()),
            2,
            "Only 2 shares are visible",
        )
        self.assertEqual(
            len(self.database.shares_get_all_with_hidden()),
            3,
            "There are 3 shares in total",
        )

    def test_last_price(self):
        # No last price
        test_name = "Missing last price should raise NoPriceException"
        share = self.database.share_get_by_id(1)
        self.assertRaises(
            NoPriceException,
            lambda _: share.last_price,
            test_name,
        )
        try:
            share.last_price
        except NoPriceException as e:
            self.assertEqual(e.share, share, test_name + " - exception.share is wrong")

        # Last price exists
        last_price = self.database.share_get_by_id(2).last_price
        self.assertEqual(last_price.price, 550, "Last price should be 550 USD")
        self.assertEqual(last_price.currency, "USD", "Last price should be 550 USD")
        self.assertEqual(last_price.source, "Second test", "Last price is Second test")

    def test_validations(self):
        share = Share(id=1, name="Test share", main_code="FE4451", base_currency="EUR")

        # Test empty share name
        test_name = "Share must have a non-empty name"
        with self.assertRaises(ValidationException) as cm:
            share.name = ""
        self.assertEqual(type(cm.exception), ValidationException, test_name)
        self.assertEqual(
            cm.exception.item,
            share,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "name",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "",
            test_name + " - exception.invalid_value is wrong",
        )

        # Test None share name
        test_name = "Share must have a name that is not None"
        with self.assertRaises(ValidationException) as cm:
            share.name = None
        self.assertEqual(type(cm.exception), ValidationException, test_name)
        self.assertEqual(
            cm.exception.item,
            share,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "name",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            None,
            test_name + " - exception.invalid_value is wrong",
        )

        # Test share name max length
        test_name = "Share can't have a name with more than 250 characters"
        with self.assertRaises(ValidationException) as cm:
            share.name = "a" * 251
        self.assertEqual(
            type(cm.exception),
            ValidationException,
            test_name,
        )
        self.assertEqual(
            cm.exception.item,
            share,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "name",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "a" * 251,
            test_name + " - exception.invalid_value is wrong",
        )

        # Test share main code max length
        test_name = "Share can't have a main code with more than 250 characters"
        with self.assertRaises(ValidationException) as cm:
            share.main_code = "a" * 251
        self.assertEqual(
            type(cm.exception),
            ValidationException,
            test_name,
        )
        self.assertEqual(
            cm.exception.item,
            share,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "main_code",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "a" * 251,
            test_name + " - exception.invalid_value is wrong",
        )
