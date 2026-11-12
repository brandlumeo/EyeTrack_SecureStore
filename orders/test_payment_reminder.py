from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from store.models import Category, Product

from .models import Order, OrderItem


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", SITE_URL="https://shop.example/")
class PaymentReminderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", email="buyer@example.com", password="StrongPass123!")
        cat = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(category=cat, name="Dome Camera", description="x", price="2799.00", stock=5)

    def order(self, hours_ago, user=True, method=Order.PaymentMethod.ONLINE, paid=False, email="buyer@example.com"):
        o = Order.objects.create(user=self.user if user else None, full_name="Asha", email=email, phone="9999999999",
                                 address="Kozhikode", total="2799.00", payment_method=method,
                                 payment_status=Order.PaymentStatus.PAID if paid else Order.PaymentStatus.PENDING,
                                 order_status=Order.OrderStatus.CONFIRMED if paid else Order.OrderStatus.PENDING)
        OrderItem.objects.create(order=o, product=self.product, quantity=1, price="2799.00")
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(hours=hours_ago))
        return o

    def run_command(self, *args):
        out = StringIO()
        call_command("remind_unpaid_orders", *args, stdout=out)
        return out.getvalue()

    def test_reminder_sent_once_with_pay_link_and_hold_time(self):
        o = self.order(hours_ago=3)
        self.assertIn("reminded %s" % o.formatted_id, self.run_command())
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["buyer@example.com"])
        self.assertIn(o.formatted_id, msg.subject)
        self.assertIn("https://shop.example" + reverse("razorpay_checkout", args=[o.pk]), msg.body)
        self.assertIn("1 x Dome Camera", msg.body)
        self.assertIn("nothing will be charged", msg.body)
        html = msg.alternatives[0][0]
        self.assertIn("Pay now", html)
        o.refresh_from_db()
        self.assertIsNotNone(o.payment_reminder_sent_at)
        self.run_command()
        self.assertEqual(len(mail.outbox), 1)  # never twice

    def test_only_due_account_orders_get_a_reminder(self):
        skip = [self.order(hours_ago=1),                                    # too early
                self.order(hours_ago=23.5),                                 # about to be released
                self.order(hours_ago=3, paid=True),                         # paid
                self.order(hours_ago=3, method=Order.PaymentMethod.COD),    # cash on delivery
                self.order(hours_ago=3, user=False),                        # guest: can't pay from another browser
                self.order(hours_ago=3, email="")]                          # no email
        self.assertIn("0 payment reminder(s) sent", self.run_command())
        self.assertEqual(len(mail.outbox), 0)
        for o in skip:
            o.refresh_from_db()
            self.assertIsNone(o.payment_reminder_sent_at)

    def test_dry_run_sends_nothing(self):
        o = self.order(hours_ago=3)
        self.assertIn("would remind %s" % o.formatted_id, self.run_command("--dry-run"))
        self.assertEqual(len(mail.outbox), 0)
        o.refresh_from_db()
        self.assertIsNone(o.payment_reminder_sent_at)

    def test_pay_link_sends_signed_out_customer_to_sign_in_and_back(self):
        o = self.order(hours_ago=3)
        url = reverse("razorpay_checkout", args=[o.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])
        self.assertIn("next=" + url, r["Location"])
        # an order that doesn't exist looks the same, so the link reveals nothing
        self.assertEqual(self.client.get(reverse("razorpay_checkout", args=[999999]))["Location"].split("?")[0], r["Location"].split("?")[0])
