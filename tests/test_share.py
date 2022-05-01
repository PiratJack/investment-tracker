import datetime
import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.share import Share
from investmenttracker.models.shareprice import SharePrice
from investmenttracker.models.base import NoPriceException

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
