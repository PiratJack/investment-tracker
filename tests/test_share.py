import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import NoPriceException, ValidationException
from investmenttracker.models.share import Share
from investmenttracker.models.shareprice import SharePrice

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

    def test_gets(self):
        # Database selects & filters
        self.assertEqual(
            len(self.database.shares_query().all()),
            3,
            "There are 3 shares in total",
        )
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

        # String representation
        share = self.database.share_get_by_id(1)
        self.assertEqual(
            str(share),
            "Share AXA (FR847238, EUR, synced, enabled)",
            "Share representation is wrong",
        )
        share = Share(
            id=3,
            name="Hidden share",
            main_code="FEFZE",
            base_currency="XFE",
            hidden=True,
        )
        self.assertEqual(
            str(share),
            "Share Hidden share (FEFZE, XFE, synced, enabled)",
            "Share representation is wrong",
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

        # Test mandatory fields
        for field in ["name", "base_currency"]:
            for value in ["", None]:
                test_name = "Share must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(share, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    share,
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
        for field in ["name", "main_code"]:
            test_name = "Share " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(share, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                share,
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
