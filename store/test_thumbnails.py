import io
import pathlib
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from . import images
from .models import Category, Product, ProductGallery

MEDIA = tempfile.mkdtemp(prefix="test-thumbs-")


def tearDownModule():
    shutil.rmtree(MEDIA, ignore_errors=True)


def photo(name="cam.jpg", size=(1600, 1200), fmt="JPEG", mode="RGB"):
    buf = io.BytesIO()
    Image.new(mode, size, (30, 90, 160) if mode == "RGB" else (30, 90, 160, 128)).save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue())


@override_settings(MEDIA_ROOT=MEDIA)
class ThumbnailTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="CCTV Cameras", slug="cctv-cameras")

    def product(self, **kw):
        defaults = dict(category=self.cat, name="Dome 2MP", price="1999.00", stock=3, description="Dome")
        defaults.update(kw)
        return Product.objects.create(**defaults)

    def thumb_path(self, name, width):
        return pathlib.Path(MEDIA) / images.thumb_name(name, width)

    def test_saving_a_product_makes_webp_copies_and_keeps_the_original(self):
        p = self.product(image=photo())
        for w in (400, 800, 1200):
            path = self.thumb_path(p.image.name, w)
            self.assertTrue(path.exists(), w)
            with Image.open(path) as im:
                self.assertEqual(im.format, "WEBP")
                self.assertEqual(im.width, w)
                self.assertEqual(im.height, w * 3 // 4)
        self.assertTrue(pathlib.Path(p.image.path).exists())
        self.assertTrue(p.image.name.endswith(".jpg"))

    def test_small_photos_are_not_upscaled(self):
        p = self.product(image=photo(size=(500, 500)))
        self.assertEqual(images.make_thumbs(p.image), [400])
        self.assertFalse(self.thumb_path(p.image.name, 800).exists())

    def test_transparent_png_and_gallery_photos(self):
        p = self.product()
        g = ProductGallery.objects.create(product=p, image=photo("lock.png", (900, 900), "PNG", "RGBA"))
        with Image.open(self.thumb_path(g.image.name, 800)) as im:
            self.assertEqual(im.mode, "RGBA")

    def test_bad_or_missing_files_fall_back_to_the_original(self):
        p = self.product(image="products/not-there.jpg")
        self.assertEqual(images.make_thumbs(p.image), [])
        self.assertEqual(images.thumb_url(p.image, 400), "/media/products/not-there.jpg")
        self.assertEqual(images.thumb_url(None, 400), "")

    def test_thumb_url_picks_the_next_size_up(self):
        p = self.product(image=photo())
        self.assertTrue(images.thumb_url(p.image, 400).endswith("/400/products/" + pathlib.Path(p.image.name).stem + ".webp"))
        self.assertIn("/800/", images.thumb_url(p.image, 600))
        self.assertIn("/1200/", images.thumb_url(p.image, 2000))

    def test_catalogue_serves_webp_with_srcset(self):
        p = self.product(image=photo())
        html = self.client.get("/").content.decode()
        self.assertIn(images.thumb_name(p.image.name, 400), html)
        self.assertIn("800w", html)
        self.assertIn('sizes="(max-width: 767px)', html)

    def test_product_page_uses_large_webp_and_keeps_original_for_sharing(self):
        p = self.product(image=photo())
        html = self.client.get(reverse("product_detail", args=[p.slug])).content.decode()
        self.assertIn('src="/media/%s" id="main-detail-image"' % images.thumb_name(p.image.name, 1200), html)
        self.assertIn('og:image" content="http://testserver/media/%s"' % p.image.name, html)

    def test_command_fills_in_missing_copies(self):
        p = self.product(image=photo())
        for w in (400, 800, 1200):
            self.thumb_path(p.image.name, w).unlink()
        out = io.StringIO()
        call_command("make_thumbnails", stdout=out)
        self.assertTrue(self.thumb_path(p.image.name, 400).exists())
        self.assertIn("Photos with WebP copies: 1", out.getvalue())

    def test_stock_updates_do_not_reprocess_the_photo(self):
        p = self.product(image=photo())
        path = self.thumb_path(p.image.name, 400)
        before = path.stat().st_mtime_ns
        p.stock = 1
        p.save()
        self.assertEqual(path.stat().st_mtime_ns, before)
