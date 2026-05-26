from smtplib import SMTPAuthenticationError
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Profile
from orders.models import Invoice, Order, OrderItem, Shipment
from store.models import Category, Product


class AccountOrderHistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(
            category=self.category,
            name="Bullet Camera",
            description="Outdoor camera",
            price="1999.00",
            stock=5,
            is_available=True,
            image="products/test.jpg",
        )

    def test_order_history_lists_track_order_actions(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9999999999",
            address="Kozhikode, Kerala",
            total="1999.00",
            order_status=Order.OrderStatus.CONFIRMED,
            shipping_status=Order.ShippingStatus.IN_TRANSIT,
            tracking_number="TRACK-12345",
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price="1999.00")
        Shipment.objects.create(order=order, carrier="BlueDart", service_level="Air Express")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_history"))

        self.assertContains(response, "In Transit")
        self.assertContains(response, reverse("order_tracking", args=[order.id]))
        self.assertContains(response, reverse("order_invoice", args=[order.id]))
        self.assertContains(response, "Track Order")
        self.assertContains(response, "Invoice")

    def test_order_history_handles_missing_tracking_details(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9999999999",
            address="Kozhikode, Kerala",
            total="1999.00",
            order_status=Order.OrderStatus.PENDING,
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price="1999.00")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_history"))

        self.assertContains(response, "Available after dispatch")

    def test_order_tracking_page_shows_selected_order_details(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9999999999",
            address="Kozhikode, Kerala",
            total="1999.00",
            order_status=Order.OrderStatus.CONFIRMED,
            shipping_status=Order.ShippingStatus.IN_TRANSIT,
            tracking_number="TRACK-12345",
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price="1999.00")
        Shipment.objects.create(order=order, carrier="BlueDart", service_level="Air Express")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_tracking", args=[order.id]))

        self.assertContains(response, "Track Your Order")
        self.assertContains(response, "TRACK-12345")
        self.assertContains(response, "BlueDart")
        self.assertContains(response, "Air Express")
        self.assertContains(response, "Current stage")
        self.assertContains(response, "Subtotal")

    def test_order_tracking_page_formats_customer_facing_fields(self):
        order = Order.objects.create(
            user=self.user,
            full_name="shamil cv",
            email="customer@example.com",
            phone="9999999999",
            address="  huhsaldkasj,  kkjddlha, , kkl  ",
            total="1999.00",
            order_status=Order.OrderStatus.CONFIRMED,
            payment_status="Paid",
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price="1999.00")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_tracking", args=[order.id]))

        self.assertContains(response, "Recipient")
        self.assertContains(response, "Shamil Cv")
        self.assertContains(response, "huhsaldkasj, kkjddlha, kkl")
        self.assertContains(response, "Not assigned yet")
        self.assertContains(response, "Paid")

    def test_order_invoice_page_shows_invoice_details(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9999999999",
            address="Kozhikode, Kerala",
            total="2657.82",
            order_status=Order.OrderStatus.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price="1999.00")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_invoice", args=[order.id]))

        invoice = Invoice.objects.get(order=order)
        self.assertContains(response, invoice.invoice_number)
        self.assertContains(response, "Tax Invoice")
        self.assertContains(response, "Download PDF")
        self.assertContains(response, "Customer Name")
        self.assertContains(response, "Bullet Camera")

    def test_order_invoice_download_returns_pdf(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9999999999",
            address="Kozhikode, Kerala",
            total="2657.82",
            order_status=Order.OrderStatus.CONFIRMED,
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price="1999.00")
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_invoice_download", args=[order.id]))

        invoice = Invoice.objects.get(order=order)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(invoice.invoice_number.lower(), response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-1.4"))

    def test_order_tracking_page_is_user_scoped(self):
        other_user = User.objects.create_user(
            username="othercustomer",
            email="other@example.com",
            password="StrongPass123!",
        )
        order = Order.objects.create(
            user=other_user,
            full_name="Other Customer",
            email="other@example.com",
            phone="8888888888",
            address="Other Address",
            total="1000.00",
            order_status=Order.OrderStatus.CONFIRMED,
        )
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_tracking", args=[order.id]))

        self.assertEqual(response.status_code, 404)

    def test_order_invoice_page_is_user_scoped(self):
        other_user = User.objects.create_user(
            username="otherinvoiceuser",
            email="otherinvoice@example.com",
            password="StrongPass123!",
        )
        order = Order.objects.create(
            user=other_user,
            full_name="Other Customer",
            email="other@example.com",
            phone="8888888888",
            address="Other Address",
            total="1000.00",
            order_status=Order.OrderStatus.CONFIRMED,
        )
        self.client.login(username="customer", password="StrongPass123!")

        response = self.client.get(reverse("order_invoice", args=[order.id]))

        self.assertEqual(response.status_code, 404)


class AccountEmailFailureTests(TestCase):
    def test_register_rolls_back_when_verification_email_fails(self):
        with patch(
            "accounts.views.send_verification_email",
            side_effect=SMTPAuthenticationError(535, b"bad credentials"),
        ):
            response = self.client.post(
                reverse("register"),
                data={
                    "first_name": "Shamil",
                    "last_name": "Cv",
                    "email": "newcustomer@example.com",
                    "phone_number": "9999999999",
                    "password1": "StrongPass123!",
                    "password2": "StrongPass123!",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We could not send the verification email right now.")
        self.assertFalse(User.objects.filter(email="newcustomer@example.com").exists())

    def test_profile_email_change_rolls_back_when_verification_email_fails(self):
        user = User.objects.create_user(
            username="profileuser",
            email="customer@example.com",
            password="StrongPass123!",
            first_name="Current",
            last_name="User",
            is_active=True,
        )
        Profile.objects.create(user=user, phone_number="9999999999", email_verified=True)
        self.client.login(username="profileuser", password="StrongPass123!")

        with patch(
            "accounts.views.send_verification_email",
            side_effect=SMTPAuthenticationError(535, b"bad credentials"),
        ):
            response = self.client.post(
                reverse("profile"),
                data={
                    "first_name": "Current",
                    "last_name": "User",
                    "email": "newmail@example.com",
                    "phone_number": "9999999999",
                },
            )

        user.refresh_from_db()
        profile = Profile.objects.get(user=user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We could not send the verification email to your new address.")
        self.assertEqual(user.email, "customer@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(profile.email_verified)

    def test_resend_verification_email_sends_for_inactive_user(self):
        user = User.objects.create_user(
            username="inactiveuser",
            email="inactive@example.com",
            password="StrongPass123!",
            is_active=False,
        )

        response = self.client.post(
            reverse("resend_verification_email"),
            data={"email": user.email},
        )

        self.assertRedirects(response, reverse("verify_email_sent"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn("Verify your Eyetrack Solutions account", mail.outbox[0].subject)

    def test_resend_verification_redirects_verified_user_to_login(self):
        user = User.objects.create_user(
            username="verifieduser",
            email="verified@example.com",
            password="StrongPass123!",
            is_active=True,
        )

        response = self.client.post(
            reverse("resend_verification_email"),
            data={"email": user.email},
            follow=True,
        )

        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, "This email is already verified. Please sign in.")
        self.assertEqual(len(mail.outbox), 0)

    def test_register_duplicate_inactive_email_shows_resend_link(self):
        User.objects.create_user(
            username="pendinguser",
            email="pending@example.com",
            password="StrongPass123!",
            is_active=False,
        )

        response = self.client.post(
            reverse("register"),
            data={
                "first_name": "Pending",
                "last_name": "User",
                "email": "pending@example.com",
                "phone_number": "9999999999",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("resend_verification_email"))
        self.assertContains(response, "already registered but not verified")
        self.assertContains(response, "Use the resend verification email option below.")
