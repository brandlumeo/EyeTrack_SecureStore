from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from orders.models import Order
from .models import Category, Product


class StoreFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Camera",
            description="Demo camera",
            price="1000.00",
            stock=1,
            is_available=True,
            image="products/test.jpg",
        )
        self.user = User.objects.create_user(username="buyer", email="buyer@example.com", password="StrongPass123!")

    def test_add_to_cart_requires_post(self):
        response = self.client.get(reverse("add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_respects_stock_limit(self):
        self.client.post(reverse("add_to_cart", args=[self.product.id]))
        self.client.post(reverse("add_to_cart", args=[self.product.id]))
        session = self.client.session
        self.assertEqual(session["cart"][str(self.product.id)], 1)

    def test_checkout_prevents_order_when_stock_insufficient(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()
        self.client.login(username="buyer", password="StrongPass123!")

        response = self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Buyer Test",
                "email": "buyer@example.com",
                "phone": "9999999999",
                "address": "Sample Address",
            },
        )

        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(Order.objects.count(), 0)

    def test_simulated_payment_reduces_stock_and_completes_order(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        checkout_response = self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Buyer Test",
                "email": "buyer@example.com",
                "phone": "9999999999",
                "address": "Sample Address",
            },
        )
        order = Order.objects.get()
        self.assertRedirects(checkout_response, reverse("simulated_payment", args=[order.id]))

        payment_response = self.client.post(reverse("simulated_payment", args=[order.id]))
        self.assertRedirects(payment_response, reverse("order_success"))

        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertEqual(order.status, "Completed")
