from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Notification
from store.models import Category, Product

from . import stock
from .models import Order, OrderItem


class ReleaseUnpaidOrdersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", email="buyer@example.com", password="StrongPass123!")
        cat = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(category=cat, name="Dome Camera", description="x", price="1000.00", stock=8)

    def order(self, hours_ago, method=Order.PaymentMethod.ONLINE, paid=False, qty=2):
        """An order as checkout leaves it: stock already taken (10 -> 8 for the default)."""
        o = Order.objects.create(user=self.user, full_name="Buyer", email="buyer@example.com", phone="9999999999",
                                 address="Kozhikode", total="2000.00", payment_method=method,
                                 payment_status=Order.PaymentStatus.PAID if paid else Order.PaymentStatus.PENDING,
                                 order_status=Order.OrderStatus.CONFIRMED if paid else Order.OrderStatus.PENDING)
        OrderItem.objects.create(order=o, product=self.product, quantity=qty, price="1000.00")
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(hours=hours_ago))
        return o

    def run_command(self, *args):
        out = StringIO()
        call_command("release_unpaid_orders", *args, stdout=out)
        return out.getvalue()

    @patch("orders.signals.send_email_async")
    def test_old_unpaid_online_order_is_released_quietly(self, send):
        o = self.order(hours_ago=25)
        out = self.run_command()
        self.assertIn("released %s" % o.formatted_id, out)
        o.refresh_from_db()
        self.assertEqual((o.order_status, o.payment_status), (Order.OrderStatus.CANCELLED, Order.PaymentStatus.FAILED))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)  # the 2 held units are back
        send.assert_not_called()  # no customer or staff emails
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Notification.objects.exists())  # no in-app notification either
        self.assertIn("0 unpaid order(s) released", self.run_command())  # nothing left; running again is harmless

    def test_recent_paid_and_cod_orders_are_left_alone(self):
        keep = [self.order(hours_ago=2), self.order(hours_ago=48, paid=True),
                self.order(hours_ago=48, method=Order.PaymentMethod.COD)]
        self.assertIn("0 unpaid order(s) released", self.run_command())
        for o in keep:
            before = o.order_status
            o.refresh_from_db()
            self.assertEqual(o.order_status, before)
        self.assertIn("released", self.run_command("--hours", "1"))  # a shorter hold catches the 2-hour-old one

    def test_dry_run_changes_nothing(self):
        o = self.order(hours_ago=30)
        out = self.run_command("--dry-run")
        self.assertIn("would release %s" % o.formatted_id, out)
        self.assertIn("2 x Dome Camera", out)
        o.refresh_from_db()
        self.assertEqual(o.order_status, Order.OrderStatus.PENDING)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_released_order_cannot_start_a_new_payment(self):
        o = self.order(hours_ago=30)
        self.run_command()
        self.client.login(username="buyer", password="StrongPass123!")
        r = self.client.get(reverse("razorpay_checkout", args=[o.pk]))
        self.assertRedirects(r, reverse("order_history"), fetch_redirect_response=False)

    def test_payment_arriving_after_release_takes_the_stock_again(self):
        o = self.order(hours_ago=30)
        self.run_command()
        o.refresh_from_db()
        stock.retake_stock_if_cancelled(o)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        stock.retake_stock_if_cancelled(self.order(hours_ago=1, paid=True))  # not cancelled: no change
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
