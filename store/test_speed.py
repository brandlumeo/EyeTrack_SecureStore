import pathlib
import shutil
import tempfile

from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings

from .models import Category, Product

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class SpeedTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_media_is_browser_cacheable_and_sets_no_cookie(self):
        (pathlib.Path(MEDIA) / "products").mkdir(exist_ok=True)
        (pathlib.Path(MEDIA) / "products" / "cam.webp").write_bytes(b"RIFF....WEBP")
        r = self.client.get("/media/products/cam.webp")
        self.assertEqual(r.status_code, 200)
        self.assertIn("max-age=604800", r["Cache-Control"])
        self.assertIn("public", r["Cache-Control"])
        self.assertNotIn("no-store", r["Cache-Control"])
        self.assertNotIn("sessionid", r.cookies)
        b"".join(r.streaming_content)

    def test_pages_stay_uncached_and_anonymous_visits_create_no_session(self):
        r = self.client.get("/")
        self.assertIn("no-store", r["Cache-Control"])
        self.assertNotIn("sessionid", r.cookies)
        self.assertEqual(Session.objects.count(), 0)

    def test_light_logo_and_lazy_product_images(self):
        cat = Category.objects.create(name="CCTV Cameras", slug="cctv-installation")
        for n in range(5):
            Product.objects.create(category=cat, name=f"Cam {n}", price="1000.00", stock=1, description="x", image=f"products/c{n}.jpg")
        home = self.client.get("/").content.decode()
        self.assertIn("img/company-logo-sm.webp", home)
        self.assertNotIn("img/company-logo.png\" as=\"image\"", home)
        self.assertNotIn('class="product-image" decoding', home)  # every homepage card image is lazy
        listing = self.client.get("/category/cctv-installation/").content.decode()
        self.assertEqual(listing.count('class="product-image" loading="lazy"'), 2)  # first 3 load straight away
