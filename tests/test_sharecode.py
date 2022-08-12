import os
import unittest

import investmenttracker.models.database as databasemodel

from investmenttracker.models.base import ValidationException
from investmenttracker.models.share import Share
from investmenttracker.models.sharecode import ShareCode

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestShareCode(unittest.TestCase):
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
                ShareCode(share_id=1, origin="boursorama", value="1rACN"),
                ShareCode(share_id=1, origin="quantalys", value="14587"),
                ShareCode(share_id=1, origin="alphavantage", value="FR4941"),
                ShareCode(share_id=2, origin="quantalys", value="478924"),
                ShareCode(share_id=2, origin="alphavantage", value="NYSE:ACN"),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        share = self.database.share_get_by_id(1)
        share_code = share.codes[0]
        self.assertEqual(
            len(share.codes),
            3,
            "ACN share must have 3 codes",
        )

        self.assertEqual(
            str(share_code),
            "ShareCode AXA (1rACN @ Boursorama)",
            "ShareCode representation is wrong",
        )
        share_code = ShareCode(
            share_id=2,
            value="EFEZ",
        )
        self.assertEqual(
            str(share_code),
            "ShareCode (EFEZ @ None)",
            "ShareCode representation is wrong",
        )

        # Search shares by various fields
        share = self.database.share_search("AXA")
        self.assertEqual(
            len(share),
            1,
            "Only 1 result found by searching 'AXA' (found through name)",
        )
        self.assertEqual(
            share[0].id,
            1,
            "Share 1 found by searching 'AXA' (found through name)",
        )

        share = self.database.share_search("FR847238")
        self.assertEqual(
            len(share),
            1,
            "Only 1 result found by searching 'FR847238' (found through main code)",
        )
        self.assertEqual(
            share[0].id,
            1,
            "Share 1 found by searching 'FR847238' (found through main code)",
        )
        share = self.database.share_search("FR4941")
        self.assertEqual(
            len(share),
            1,
            "Only 1 result found by searching 'FR4941' (found through code)",
        )
        self.assertEqual(
            share[0].id,
            1,
            "Share 1 found by searching 'FR4941' (found through code)",
        )
        # Check search returns a single share, even if it matches through different means
        share = self.database.share_search("NYSE:ACN")
        self.assertEqual(
            len(share),
            1,
            "Only 1 result found by searching 'NYSE:ACN' (should not yield duplicates)",
        )
        # Check search returns a single share based on ID
        share = self.database.share_search(2)
        self.assertEqual(
            len(share),
            1,
            "Only 1 result found by searching 2",
        )

    def test_validations(self):
        share_code = self.database.share_get_by_id(1).codes[0]

        # Test mandatory fields
        for field in ["share_id", "origin", "value"]:
            for value in ["", None]:
                test_name = "Share code must have a " + field + " that is not "
                test_name += "None" if value == None else "empty"
                with self.assertRaises(ValidationException) as cm:
                    setattr(share_code, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    share_code,
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
        for field in ["origin", "value"]:
            test_name = "Share code " + field + " can't be more than 250 characters"
            value = "a" * 251
            with self.assertRaises(ValidationException) as cm:
                setattr(share_code, field, value)
            self.assertEqual(type(cm.exception), ValidationException, test_name)
            self.assertEqual(
                cm.exception.item,
                share_code,
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