import datetime
import os
import unittest

import sqlalchemy.orm.exc
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
                Share(id=1, name="AXA", main_code="FR847238", base_currency_id=5),
                Share(id=2, name="Accenture", main_code="NYSE:ACN", base_currency_id=6),
                Share(id=3, name="Workday", main_code="WDAY", base_currency_id=6),
                Share(id=4, name="HSBC", main_code="LU4325", base_currency_id=5),
                Share(id=5, name="Euro", main_code="EUR"),
                Share(id=6, name="Dollar", main_code="USD"),
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
                SharePrice(
                    share_id=3,
                    date=datetime.datetime(2022, 1, 1),
                    price=100,
                    currency="USD",
                    source="Test gets",
                ),
                SharePrice(
                    share_id=3,
                    date=datetime.datetime(2022, 2, 1),
                    price=120,
                    currency="USD",
                    source="Test gets",
                ),
                SharePrice(
                    share_id=3,
                    date=datetime.datetime(2022, 3, 1),
                    price=130,
                    currency="USD",
                    source="Test gets",
                ),
                SharePrice(
                    share_id=3,
                    date=datetime.datetime(2022, 4, 1),
                    price=140,
                    currency="USD",
                    source="Test gets",
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        # Get from direct query (based on date)
        share_prices = self.database.share_price_query()
        share_prices = share_prices.filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        )

        self.assertEqual(
            len(share_prices.all()),
            3,
            "There are 3 prices after March 1st, 2022",
        )

        # Get from direct query (based on share)
        share_prices = self.database.share_price_query()
        share_prices = share_prices.filter(SharePrice.share_id == 3)
        self.assertEqual(
            len(share_prices.all()),
            4,
            "There are 4 prices for Workday",
        )

        # Get from direct query (based on share + date)
        share_prices = self.database.share_price_query()
        share_prices = share_prices.filter(SharePrice.share_id == 3).filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        )
        self.assertEqual(
            len(share_prices.all()),
            2,
            "There are 2 prices for Workday after March 1st, 2022",
        )

        # Get from share
        share = self.database.share_get_by_id(2)
        share_prices = share.prices
        self.assertEqual(
            len(share_prices),
            2,
            "Share Accenture has 2 prices",
        )

        # String representation
        share_price = self.database.share_price_get_by_id(1)
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

    def test_delete(self):
        # Get from direct query (based on date)
        share_prices = self.database.share_price_query()
        share_prices = share_prices.filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        ).all()

        nb_before_delete = len(share_prices)

        self.database.share_price_delete(share_prices[0])
        share_prices = self.database.share_price_query()
        share_prices = share_prices.filter(
            SharePrice.date >= datetime.datetime(2022, 3, 1).date()
        ).all()

        self.assertEqual(
            len(share_prices),
            nb_before_delete - 1,
            "Price deletion didn't reduce the number of elements",
        )

        self.assertRaises(
            sqlalchemy.orm.exc.NoResultFound,
            lambda _: self.database.share_price_get_by_id(2),
            "Price deletion didn't delete the item",
        )
