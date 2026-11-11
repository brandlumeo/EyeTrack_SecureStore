from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order

from . import serviceability
from .models import Category, PincodeLookup, Product, ServiceableArea

# What India Post returns for these pincodes (district, state); None = unknown / service down.
INDIA_POST = {
    "673522": ("Kozhikode", "Kerala"),
    "670001": ("Kannur", "Kerala"),
    "676505": ("Malappuram", "Kerala"),
    "673121": ("Wayanad", "Kerala"),
    "679303": ("Palakkad", "Kerala"),
    "110001": ("Central Delhi", "Delhi"),
}


def fake_fetch(pincode):
    return INDIA_POST.get(pincode)


@patch("store.serviceability._fetch", side_effect=fake_fetch)
class ServiceabilityRulesTests(TestCase):
    def test_installation_only_in_our_three_districts(self, fetch):
        for pin, installs, days in [("673522", True, 5), ("670001", True, 7), ("676505", True, 7),
                                    ("673121", False, 7), ("679303", False, 7), ("110001", False, 7)]:
            r = serviceability.check(pin)
            self.assertTrue(r.delivery_available, pin)
            self.assertEqual(r.installation_available, installs, pin)
            self.assertEqual(r.estimated_days, days, pin)
            self.assertEqual(r.delivery_charge, Decimal("0.00"), pin)

    def test_each_pincode_is_looked_up_once(self, fetch):
        serviceability.check("670001")
        serviceability.check("670001")
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(PincodeLookup.objects.get(pincode="670001").district, "Kannur")

    def test_lookup_failure_still_delivers_but_cannot_confirm_installation(self, fetch):
        r = serviceability.check("695001")  # not in the fake India Post data
        self.assertTrue(r.delivery_available)
        self.assertFalse(r.installation_available)
        self.assertTrue(r.installation_unverified)
        self.assertFalse(PincodeLookup.objects.filter(pincode="695001").exists())  # retried next time

    def test_invalid_pincodes(self, fetch):
        for pin in ("", "12345", "012345", "912345", "67352a"):
            self.assertFalse(serviceability.check(pin).valid, pin)
        fetch.assert_not_called()

    def test_admin_exception_wins_without_a_lookup(self, fetch):
        ServiceableArea.objects.create(pincode="673121", delivery_available=True, estimated_delivery_days=3,
                                       delivery_charge=Decimal("150.00"))
        r = serviceability.check("673121")
        self.assertTrue(r.installation_available)  # staff enabled this Wayanad pincode by hand
        self.assertEqual((r.estimated_days, r.delivery_charge), (3, Decimal("150.00")))
        fetch.assert_not_called()
        self.assertEqual(serviceability.delivery_charge("673121", Decimal("1000.00")), Decimal("150.00"))
        self.assertEqual(serviceability.delivery_charge("673121", Decimal("5000.00")), Decimal("0.00"))
        self.assertEqual(serviceability.delivery_charge("110001", Decimal("1000.00")), Decimal("0.00"))


@patch("store.serviceability._fetch", side_effect=fake_fetch)
class PincodeCheckAndCheckoutTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(category=cat, name="Dome Camera", description="x", price="1000.00", stock=5,
                                              is_available=True, installation_available=True, installation_charge="500.00")
        User.objects.create_user(username="buyer", email="buyer@example.com", password="StrongPass123!")

    def check(self, pin):
        return self.client.get(reverse("check_serviceability"), {"pincode": pin}).json()

    def test_product_page_pincode_check(self, fetch):
        kannur = self.check("670001")
        self.assertTrue(kannur["ok"])
        self.assertTrue(kannur["installation_available"])
        self.assertIn("(Kannur) in 7 days", kannur["message"])
        delhi = self.check("110001")
        self.assertTrue(delhi["ok"])
        self.assertFalse(delhi["installation_available"])
        self.assertIn("Delivery only", delhi["message"])
        self.assertIn("Kannur, Kozhikode, Malappuram", delhi["message"])

    def order(self, pin, install=False):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        if install:
            session["cart_installations"] = {str(self.product.id): True}
        session.save()
        data = {"full_name": "Buyer", "email": "buyer@example.com", "phone": "9999999999", "addr_house": "1 Main St",
                "addr_street": "Road", "addr_city": "City", "addr_state": "State", "addr_pincode": pin}
        if install:
            data.update(installation_date=(date.today() + timedelta(days=3)).isoformat(),
                        installation_time="Morning (9 AM - 1 PM)")
        return self.client.post(reverse("checkout"), data=data)

    def test_orders_from_anywhere_in_india_go_through(self, fetch):
        for pin in ("679303", "110001"):
            self.order(pin)
        self.assertEqual(Order.objects.count(), 2)
        # free delivery for now: a Rs 1,000 order costs Rs 1,000 (no fallback shipping fee)
        self.assertEqual({o.total for o in Order.objects.all()}, {Decimal("1000.00")})

    def test_installation_orders_only_in_our_districts(self, fetch):
        self.order("676505", install=True)  # Malappuram
        self.assertEqual(Order.objects.count(), 1)
        r = self.order("673121", install=True)  # Wayanad
        self.assertRedirects(r, reverse("checkout"), fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(), 1)
        page = self.client.get(reverse("checkout")).content.decode()
        self.assertIn("installation is available in Kannur, Kozhikode, Malappuram districts", page)
