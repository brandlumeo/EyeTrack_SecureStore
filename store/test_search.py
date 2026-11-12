from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class SearchRankingTests(TestCase):
    def setUp(self):
        cctv, _ = Category.objects.get_or_create(slug="cctv-installation", defaults={"name": "CCTV Cameras"})
        bio, _ = Category.objects.get_or_create(name="Biometric Devices", defaults={"slug": "biometric-devices"})
        # Biometric terminals mention CCTV in their description and have more stock, so they used to come first.
        self.terminal = Product.objects.create(category=bio, name="Face Recognition Terminal", price="13500.00", stock=50,
                                               description="Works alongside your CCTV system.")
        self.dome = Product.objects.create(category=cctv, name="CP Plus 2MP Dome Camera", price="2799.00", stock=5,
                                           description="Indoor dome.")
        self.bullet = Product.objects.create(category=cctv, name="Bullet Camera 4MP", price="3499.00", stock=2,
                                             description="Outdoor.")

    def suggest(self, q):
        return self.client.get(reverse("live_search"), {"q": q}).json()

    def test_category_and_name_matches_come_before_description_matches(self):
        names = [r["name"] for r in self.suggest("cct")["results"]]
        self.assertEqual(names[-1], "Face Recognition Terminal")
        self.assertEqual(set(names[:2]), {"CP Plus 2MP Dome Camera", "Bullet Camera 4MP"})

    def test_exact_and_prefix_beat_anywhere_in_name(self):
        Product.objects.create(category=self.dome.category, name="Dome", price="999.00", stock=0, description="x")
        names = [r["name"] for r in self.suggest("dome")["results"]]
        self.assertEqual(names[0], "Dome")  # exact name, even with no stock
        self.assertEqual(names[1], "CP Plus 2MP Dome Camera")

    def test_two_letters_only_match_the_start(self):
        self.assertEqual([r["name"] for r in self.suggest("bu")["results"]], ["Bullet Camera 4MP"])
        self.assertEqual(self.suggest("ra")["results"], [])  # "Camera" contains "ra", but not at the start

    def test_suggestions_include_total_and_see_all_link(self):
        data = self.suggest("cct")
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["all_url"], reverse("product_list") + "?q=cct")

    def test_results_page_uses_the_same_order(self):
        products = list(self.client.get(reverse("product_list"), {"q": "cct"}).context["products"])
        self.assertEqual(products[-1], self.terminal)
        self.assertEqual(len(products), 3)
