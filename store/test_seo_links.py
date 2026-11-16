import re

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Project
from .templatetags.area_tags import area_for

AREA_URLS = ["/cctv-installation/kozhikode/", "/cctv-installation/kannur/", "/cctv-installation/malappuram/"]


def title(html):
    return re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()


class AreaLinkTests(TestCase):
    def setUp(self):
        self.cctv = Category.objects.create(name="CCTV Cameras", slug="cctv-installation")
        self.it = Category.objects.create(name="IT Consulting", slug="it-consulting")
        self.empty = Category.objects.create(name="Alarm Systems", slug="alarm-systems")
        self.cam = Product.objects.create(category=self.cctv, name="Dome 2MP", price="1999.00", stock=3,
                                          description="Dome", installation_available=True, installation_charge="500")
        Product.objects.create(category=self.it, name="Network audit", price="5000.00", stock=1, description="Audit")

    def test_homepage_links_every_area_page(self):
        html = self.client.get("/").content.decode()
        for url in AREA_URLS:
            self.assertIn('href="%s"' % url, html)
        self.assertIn("CCTV installation across North Kerala", html)

    def test_installable_category_shows_areas_block_other_categories_do_not(self):
        html = self.client.get(reverse("products_by_category", args=["cctv-installation"])).content.decode()
        self.assertIn("CCTV Cameras installed across North Kerala", html)
        self.assertIn('href="/cctv-installation/kannur/"', html)
        html = self.client.get(reverse("products_by_category", args=["it-consulting"])).content.decode()
        self.assertNotIn("areasServedTitle", html)

    def test_product_with_installation_names_the_districts(self):
        html = self.client.get(reverse("product_detail", args=[self.cam.slug])).content.decode()
        self.assertIn('Installed across <a href="/cctv-installation/kozhikode/">Kozhikode</a>, '
                      '<a href="/cctv-installation/kannur/">Kannur</a> and '
                      '<a href="/cctv-installation/malappuram/">Malappuram</a> districts.', html)

    def test_services_page_links_areas(self):
        html = self.client.get(reverse("services_page")).content.decode()
        for url in AREA_URLS:
            self.assertIn('href="%s"' % url, html)

    def test_project_location_links_to_its_area(self):
        p = Project.objects.create(title="Shop system", site_type="shop", location="Perambra, Kozhikode",
                                   summary="Eight cameras.", cover_image="projects/x.jpg", is_published=True)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('<a href="/cctv-installation/kozhikode/">Perambra, Kozhikode</a>', html)

    def test_area_for_matches_towns_and_districts(self):
        self.assertEqual(area_for("Thalassery")["slug"], "kannur")
        self.assertEqual(area_for("near Tirur, Malappuram")["slug"], "malappuram")
        self.assertEqual(area_for("Kozhikode city")["slug"], "kozhikode")
        self.assertIsNone(area_for("Kochi"))
        self.assertIsNone(area_for(""))

    def test_sitemap_lists_only_categories_with_products(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/category/cctv-installation/", xml)
        self.assertNotIn("/category/alarm-systems/", xml)

    def test_hub_titles_fit_in_search_results(self):
        for url in (reverse("area_list"), reverse("download_list")):
            self.assertLessEqual(len(title(self.client.get(url).content.decode())), 60, url)
