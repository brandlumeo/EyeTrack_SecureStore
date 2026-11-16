from decimal import Decimal

from django.test import SimpleTestCase

from .templatetags.price_tags import inr


class InrFilterTests(SimpleTestCase):
    def test_indian_grouping(self):
        self.assertEqual(inr(Decimal("7200.00")), "7,200")
        self.assertEqual(inr(Decimal("125000")), "1,25,000")
        self.assertEqual(inr(Decimal("12345678")), "1,23,45,678")
        self.assertEqual(inr(Decimal("999")), "999")
        self.assertEqual(inr(0), "0")

    def test_paise_kept_only_when_present(self):
        self.assertEqual(inr(Decimal("1499.50")), "1,499.50")
        self.assertEqual(inr("2500.999"), "2,501")

    def test_bad_input_is_left_alone(self):
        self.assertEqual(inr(""), "")
        self.assertIsNone(inr(None))
