import json
import re

from django.test import TestCase
from django.urls import reverse

from . import serviceability
from .areas import AREAS
from .models import Category, Product, Project


def json_ld(response):
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                              response.content.decode(), re.S)]


class AreaPageTests(TestCase):
    def setUp(self):
        cctv = Category.objects.create(name="CCTV Cameras", slug="cctv-installation", icon="bi-camera-video")
        Category.objects.create(name="Alarm Systems", slug="alarm-systems")  # empty: not listed
        laptops = Category.objects.create(name="Laptops", slug="laptops")    # not an installation category
        Product.objects.create(category=cctv, name="Dome", description="x", price="2799.00", stock=3)
        Product.objects.create(category=laptops, name="ThinkPad", description="x", price="41300.00", stock=3)

    def test_areas_match_the_installation_districts(self):
        self.assertEqual({a["name"] for a in AREAS.values()}, serviceability.INSTALLATION_DISTRICTS)

    def test_each_district_page(self):
        for slug, area in AREAS.items():
            r = self.client.get(reverse("area_detail", args=[slug]))
            html = r.content.decode()
            self.assertContains(r, "<title>CCTV Installation in %s | Eyetrack Solutions</title>" % area["name"], html=False)
            self.assertContains(r, '<h1 id="area-title" class="mb-3">CCTV installation in %s</h1>' % area["name"], html=False)
            self.assertContains(r, area["towns"][1])
            self.assertContains(r, "?location=%s" % area["name"])
            self.assertIn("CCTV Cameras", html)
            self.assertNotIn("Alarm Systems", html)
            self.assertNotIn("Laptops", html)
            graph = [n for b in json_ld(r) for n in b.get("@graph", [b])]
            service = next(n for n in graph if n["@type"] == "Service")
            self.assertEqual(service["areaServed"]["name"], "%s district, Kerala" % area["name"])
            crumbs = next(n for n in graph if n["@type"] == "BreadcrumbList")
            self.assertEqual([i["name"] for i in crumbs["itemListElement"]], ["Home", "Areas we serve", area["name"]])
        kozhikode = self.client.get(reverse("area_detail", args=["kozhikode"])).content.decode()
        self.assertIn("about 5 days", kozhikode)
        self.assertIn("about 7 days", self.client.get(reverse("area_detail", args=["kannur"])).content.decode())

    def test_unknown_district_is_404(self):
        self.assertEqual(self.client.get("/cctv-installation/wayanad/").status_code, 404)

    def test_projects_in_the_district_are_shown(self):
        Project.objects.create(title="Shop in Thalassery", location="Thalassery, Kannur", summary="x",
                               cover_image="projects/x.jpg", is_published=True)
        Project.objects.create(title="Villa in Tirur", location="Tirur", summary="x", cover_image="projects/y.jpg",
                               is_published=True)
        kannur = self.client.get(reverse("area_detail", args=["kannur"])).content.decode()
        self.assertIn("Shop in Thalassery", kannur)
        self.assertNotIn("Villa in Tirur", kannur)
        self.assertIn("Villa in Tirur", self.client.get(reverse("area_detail", args=["malappuram"])).content.decode())

    def test_hub_sitemap_footer_and_survey_prefill(self):
        hub = self.client.get(reverse("area_list"))
        for slug in AREAS:
            self.assertContains(hub, reverse("area_detail", args=[slug]))
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(reverse("area_list"), sitemap)
        for slug in AREAS:
            self.assertIn(reverse("area_detail", args=[slug]), sitemap)
        self.assertIn(reverse("area_list"), self.client.get("/").content.decode())  # footer link
        form = self.client.get(reverse("quote_request"), {"location": "Kannur"}).content.decode()
        self.assertRegex(form, r'name="location"[^>]*value="Kannur"')
        business = next(n for b in json_ld(self.client.get("/")) for n in b.get("@graph", []) if n["@type"] == "ElectronicsStore")
        self.assertEqual(len(business["areaServed"]), 3)
