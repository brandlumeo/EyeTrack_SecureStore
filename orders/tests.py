from django.test import TestCase
from django.contrib.auth.models import User

from store.models import Category, Product
from .models import Order, OrderItem


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
            status="Pending",
        )
        item = OrderItem.objects.create(order=order, product=self.product, quantity=1, price="500.00")

        self.assertIn(str(order.id), str(order))
        self.assertIn(self.product.name, str(item))
