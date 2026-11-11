import json
import re

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


def json_ld(response):
    """Every JSON-LD block on the page, parsed (fails the test if any block is not valid JSON)."""
    html = response.content.decode()
    return [json.loads(block) for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def meta(response, name):
    found = re.search(r'<meta\s+(?:name|property)="%s"\s+content="([^"]*)"' % re.escape(name), response.content.decode())
    return found.group(1) if found else None


class CatalogSeoTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="CCTV Cameras", slug="cctv-installation")
        self.product = Product.objects.create(
            category=self.category, name="Dome Camera 2MP", price="1999.00", stock=5,
            description="<p>Night vision dome.</p>\n\nSKU: DC-2\nBrand: CP Plus\n" + "Long spec line. " * 30)
        Product.objects.create(category=self.category, name="Bullet Camera 4MP", price="3499.00", stock=2, description="Bullet")

    def test_homepage_is_indexable_and_describes_the_business(self):
        r = self.client.get("/")
        self.assertEqual(meta(r, "robots"), "index, follow, max-image-preview:large")
        self.assertIn("Kozhikode", r.content.decode().split("<title>")[1].split("</title>")[0])
        self.assertTrue(meta(r, "og:image").endswith(".jpg"))
        self.assertIn("img/home-hero-cctv.webp", r.content.decode())  # light WebP hero, not the 2 MB PNG
        self.assertNotIn("home-hero-cctv.png", r.content.decode())
        graph = next(b for b in json_ld(r) if "@graph" in b)["@graph"]
        business = next(n for n in graph if n["@type"] == "ElectronicsStore")
        self.assertEqual(business["openingHoursSpecification"][0]["opens"], "09:00")
        self.assertNotIn("/admin/", " ".join(business["sameAs"]))
        website = next(n for n in graph if n["@type"] == "WebSite")
        self.assertIn("{search_term_string}", website["potentialAction"]["target"]["urlTemplate"])

    def test_category_page_has_its_own_title_heading_and_breadcrumbs(self):
        url = reverse("products_by_category", args=[self.category.slug])
        r = self.client.get(url)
        html = r.content.decode()
        self.assertIn("<title>CCTV Cameras in Kozhikode, Kerala | Eyetrack Solutions</title>", html)
        self.assertIn("2 products from ₹1,999", meta(r, "description"))
        self.assertRegex(html, r'<h1 class="catalog-title[^"]*">CCTV Cameras</h1>')
        self.assertIn('<link rel="canonical"\n        href="http://testserver%s">' % url, html)
        crumbs = next(b for b in json_ld(r) if b.get("@type") == "BreadcrumbList")
        self.assertEqual([i["name"] for i in crumbs["itemListElement"]], ["Home", "CCTV Cameras"])

    def test_empty_category_is_noindex_until_it_has_products(self):
        empty = Category.objects.create(name="Alarm Systems", slug="alarm-systems")
        url = reverse("products_by_category", args=[empty.slug])
        self.assertEqual(meta(self.client.get(url), "robots"), "noindex, follow")
        Product.objects.create(category=empty, name="Siren", price="900.00", stock=1, description="Alarm")
        self.assertEqual(meta(self.client.get(url), "robots"), "index, follow, max-image-preview:large")

    def test_descriptions_fit_in_search_results(self):
        for url in ("/", reverse("products_by_category", args=[self.category.slug])):
            self.assertLessEqual(len(meta(self.client.get(url), "description")), 155, url)

    def test_filtered_and_search_views_are_noindex(self):
        url = reverse("products_by_category", args=[self.category.slug])
        self.assertEqual(meta(self.client.get(url, {"sort": "price_asc"}), "robots"), "noindex, follow")
        r = self.client.get("/", {"q": "dome"})
        self.assertEqual(meta(r, "robots"), "noindex, follow")
        self.assertIn("Results for &ldquo;dome&rdquo;", r.content.decode())

    def test_product_page_meta_and_structured_data(self):
        r = self.client.get(reverse("product_detail", args=[self.product.slug]))
        desc = meta(r, "description")
        self.assertTrue(desc.startswith("Dome Camera 2MP: ₹1,999 at Eyetrack Solutions"))
        self.assertNotIn("\n", desc)
        self.assertNotIn("<p>", desc)
        self.assertLessEqual(len(desc), 150)
        blocks = json_ld(r)
        product = next(b for b in blocks if b.get("@type") == "Product")
        self.assertNotIn("brand", product)  # products don't record their manufacturer; don't claim one
        self.assertEqual(product["offers"]["availability"], "https://schema.org/InStock")
        self.assertNotIn("aggregateRating", product)
        crumbs = next(b for b in blocks if b.get("@type") == "BreadcrumbList")
        self.assertEqual([i["name"] for i in crumbs["itemListElement"]], ["Home", "CCTV Cameras", "Dome Camera 2MP"])

    def test_robots_txt_keeps_private_areas_out(self):
        body = self.client.get("/robots.txt").content.decode()
        for path in ("/admin-dashboard/", "/support/requests/", "/api/"):
            self.assertIn("Disallow: %s" % path, body)
