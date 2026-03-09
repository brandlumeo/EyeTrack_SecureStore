from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class AccountViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", email="tester@example.com", password="StrongPass123!")

    def test_order_history_requires_authentication(self):
        response = self.client.get(reverse("order_history"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_order_history_loads_for_authenticated_user(self):
        self.client.login(username="tester", password="StrongPass123!")
        response = self.client.get(reverse("order_history"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_form_loads(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
