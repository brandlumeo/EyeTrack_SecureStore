from django.contrib.auth.models import User
from django.test import TestCase
from decimal import Decimal

from store.models import Category, Product
from .models import Invoice, Order, OrderItem, Payment, Shipment


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="orderuser", password="StrongPass123!")
        self.category = Category.objects.create(name="Recorders")
        self.product = Product.objects.create(
            category=self.category,
            name="Recorder Unit",
            description="Recorder description",
            price="500.00",
            stock=10,
            is_available=True,
            image="products/test.jpg",
        )

    def test_order_and_item_string_representation(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
        )
        item = OrderItem.objects.create(order=order, product=self.product, quantity=1, price="500.00")

        self.assertIn(str(order.id), str(order))
        self.assertIn(self.product.name, str(item))
        self.assertEqual(order.status, "Pending")

    def test_legacy_status_values_normalize_to_textchoices(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status="Completed",
        )

        order.refresh_from_db()
        self.assertEqual(order.order_status, Order.OrderStatus.DELIVERED)
        self.assertEqual(order.get_order_status_display(), "Delivered")

    def test_payment_and_shipment_models_attach_to_order(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
        )

        payment = Payment.objects.create(order=order, amount="500.00", status="Pending", payment_method="Simulation")
        shipment = Shipment.objects.create(order=order, carrier="Delhivery", service_level="Surface")

        self.assertEqual(order.payment_status, "Pending")
        self.assertEqual(order.shipping_status, Order.ShippingStatus.NOT_SHIPPED)
        self.assertIn(str(order.id), str(payment))
        self.assertIn(str(order.id), str(shipment))

    def test_tracking_number_allows_null(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
            tracking_number=None,
        )

        order.refresh_from_db()
        self.assertIsNone(order.tracking_number)

    def test_order_notes_allows_null(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
            order_notes=None,
        )

        order.refresh_from_db()
        self.assertIsNone(order.order_notes)

    def test_legacy_shipping_status_values_normalize_to_textchoices(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
            shipping_status="Shipped",
        )

        order.refresh_from_db()
        self.assertEqual(order.shipping_status, Order.ShippingStatus.IN_TRANSIT)
        self.assertEqual(order.get_shipping_status_display(), "In Transit")

    def test_legacy_payment_status_values_normalize_to_textchoices(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone="1234567890",
            address="Address",
            total="500.00",
            order_status=Order.OrderStatus.PENDING,
            payment_status="paid",
        )

        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.get_payment_status_display(), "Paid")

    def test_invoice_is_created_and_synced_from_order_data(self):
        with self.captureOnCommitCallbacks(execute=True):
            order = Order.objects.create(
                user=self.user,
                full_name="Order User",
                email="order@example.com",
                phone="1234567890",
                address="Address",
                total="889.00",
                order_status=Order.OrderStatus.PENDING,
            )
            OrderItem.objects.create(order=order, product=self.product, quantity=1, price="500.00")
            Payment.objects.create(order=order, amount="889.00", status=Order.PaymentStatus.PAID, payment_method="Simulation")

        invoice = Invoice.objects.get(order=order)

        self.assertEqual(invoice.invoice_number, f"INV-{order.id:08d}")
        self.assertEqual(invoice.user, order.user)
        self.assertEqual(invoice.subtotal, order.items.first().price)
        self.assertEqual(invoice.tax, Invoice._quantize("90.00"))
        self.assertEqual(invoice.shipping_cost, Invoice._quantize("299.00"))
        self.assertEqual(invoice.total_amount, Decimal("889.00"))
        self.assertEqual(invoice.payment_status, Order.PaymentStatus.PAID)


class FcmPushTokenCleanupTests(TestCase):
    """Push sending with a stand-in for firebase_admin.messaging (not installed in every environment)."""

    class UnregisteredError(Exception):
        pass

    class SenderIdMismatchError(Exception):
        pass

    def setUp(self):
        from accounts.models import Profile
        self.user = User.objects.create_user(username="pushuser", password="x")
        self.profile = Profile.objects.create(user=self.user, fcm_token="device-token")
        self.order = Order.objects.create(user=self.user, full_name="Push User", email="p@example.com", phone="9999999999",
                                          address="Kozhikode", total=Decimal("100.00"))

    def fake_messaging(self, send_side_effect=None):
        from types import SimpleNamespace
        from unittest.mock import Mock
        return SimpleNamespace(
            Message=Mock(), Notification=Mock(), send=Mock(side_effect=send_side_effect),
            UnregisteredError=self.UnregisteredError, SenderIdMismatchError=self.SenderIdMismatchError,
        )

    def send(self, messaging):
        from unittest.mock import patch
        from orders import signals
        with patch.object(signals, "messaging", messaging), patch.object(signals, "is_firebase_ready", return_value=True):
            signals._send_fcm_notification(self.order.id, Order.OrderStatus.SHIPPED)

    def test_successful_send_keeps_token(self):
        messaging = self.fake_messaging()
        self.send(messaging)
        messaging.send.assert_called_once()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.fcm_token, "device-token")

    def test_unregistered_or_mismatched_token_is_cleared(self):
        for error in (self.UnregisteredError, self.SenderIdMismatchError):
            with self.subTest(error=error.__name__):
                self.profile.fcm_token = "device-token"
                self.profile.save(update_fields=["fcm_token"])
                self.send(self.fake_messaging(send_side_effect=error("gone")))
                self.profile.refresh_from_db()
                self.assertIsNone(self.profile.fcm_token)

    def test_temporary_failure_keeps_token(self):
        self.send(self.fake_messaging(send_side_effect=RuntimeError("network down")))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.fcm_token, "device-token")
