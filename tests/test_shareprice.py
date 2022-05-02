import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException
from investmenttracker.models.share import Share
from investmenttracker.models.shareprice import SharePrice

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestSharePrice(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Share(id=1, name="AXA", main_code="FR847238", base_currency="EUR"),
                Share(
                    id=2, name="Accenture", main_code="NYSE:ACN", base_currency="USD"
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

    def test_gets(self):
        share = self.database.share_get_by_id(2)
        share_prices = share.prices
        self.assertEqual(
            len(share_prices),
            2,
            "Share Accenture has 2 prices",
        )

        # String representation
        share_price = share_prices[0]
        self.assertEqual(
            str(share_price),
            "Price (Accenture at 458.0 EUR on 2022-01-01)",
            "Share price representation is wrong",
        )

        share_price = SharePrice(
            share_id=1,
            date=datetime.datetime(2022, 4, 1),
            currency="USD",
            source="Second test",
        )
        self.assertEqual(
            str(share_price),
            "Price (Unknown on 2022-04-01 00:00:00)",
            "Share price representation is wrong",
        )

        share_price = SharePrice(
            share_id=1,
            price=125,
            source="Second test",
        )

        self.assertEqual(
            str(share_price),
            "Price (Unknown)",
            "Share price representation is wrong",
        )

    def test_validations(self):
        share_price = SharePrice(
            share_id=1,
            date=datetime.datetime(2022, 4, 1),
            price=125.24,
            currency="EUR",
            source="Test suite",
        )

        # Test mandatory fields
        for field in ["share_id", "date", "price", "currency", "source"]:
            for value in ["", None]:
                test_name = "Share price must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(share_price, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    share_price,
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

        # Test share price source max length
        test_name = "Share price can't have a source with more than 250 characters"
        with self.assertRaises(ValidationException) as cm:
            share_price.source = "a" * 251
        self.assertEqual(
            type(cm.exception),
            ValidationException,
            test_name,
        )
        self.assertEqual(
            cm.exception.item,
            share_price,
            test_name + " - exception.item is wrong",
        )
        self.assertEqual(
            cm.exception.key,
            "source",
            test_name + " - exception.key is wrong",
        )
        self.assertEqual(
            cm.exception.invalid_value,
            "a" * 251,
            test_name + " - exception.invalid_value is wrong",
        )
