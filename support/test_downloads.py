import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Download

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class DownloadCentreTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.customer = User.objects.create_user("cust", password="x")

    @staticmethod
    def drain(response):
        """Read a FileResponse body. (response.close() would fire request_finished and end the test's DB connection.)"""
        return b"".join(response.streaming_content)

    def pdf(self, name="manual.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")

    def test_list_filters_and_hides_unpublished(self):
        Download.objects.create(title="NVR manual", kind="manual", brand="Hikvision", file=self.pdf())
        Download.objects.create(title="Dome datasheet", kind="datasheet", brand="Dahua", external_url="https://example.com/ds")
        Download.objects.create(title="Secret draft", kind="manual", file=self.pdf("draft.pdf"), is_published=False)
        page = self.client.get(reverse("download_list"))
        self.assertContains(page, "NVR manual")
        self.assertContains(page, "Dome datasheet")
        self.assertNotContains(page, "Secret draft")
        self.assertContains(page, "index, follow")
        by_type = self.client.get(reverse("download_list"), {"type": "datasheet"})
        self.assertNotContains(by_type, "NVR manual")
        self.assertContains(by_type, "noindex, follow")
        self.assertContains(self.client.get(reverse("download_list"), {"brand": "Hikvision"}), "NVR manual")
        self.assertNotContains(self.client.get(reverse("download_list"), {"q": "dome"}), "NVR manual")
        self.assertContains(self.client.get(reverse("download_list"), {"q": "zzz"}), "Nothing matches")

    def test_empty_centre_offers_whatsapp(self):
        self.assertContains(self.client.get(reverse("download_list")), "being set up")

    def test_download_counts_and_serves_or_redirects(self):
        doc = Download.objects.create(title="NVR Manual", kind="manual", file=self.pdf())
        link = Download.objects.create(title="App", kind="app", external_url="https://example.com/app")
        r = self.client.get(doc.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertIn('inline; filename="nvr-manual.pdf"', r["Content-Disposition"])
        self.assertEqual(self.drain(r), b"%PDF-1.4 test")
        r = self.client.get(link.get_absolute_url())
        self.assertRedirects(r, "https://example.com/app", fetch_redirect_response=False)
        doc.refresh_from_db(); link.refresh_from_db()
        self.assertEqual((doc.download_count, link.download_count), (1, 1))

    def test_hidden_download_is_404_except_for_staff(self):
        doc = Download.objects.create(title="Hidden", file=self.pdf(), is_published=False)
        self.assertEqual(self.client.get(doc.get_absolute_url()).status_code, 404)
        self.client.force_login(self.staff)
        r = self.client.get(doc.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.drain(r)
        doc.refresh_from_db()
        self.assertEqual(doc.download_count, 0)  # staff previews are not counted

    def test_staff_manage_downloads(self):
        self.client.force_login(self.customer)
        self.assertNotEqual(self.client.get(reverse("admin_dashboard:downloads_overview")).status_code, 200)
        self.client.force_login(self.staff)
        add = reverse("admin_dashboard:download_add")
        # Needs a file or a link, and rejects unsafe file types.
        self.assertContains(self.client.post(add, {"title": "X", "kind": "manual", "order": 0}), "Upload a file or enter a link")
        bad = SimpleUploadedFile("page.html", b"<script>alert(1)</script>", content_type="text/html")
        self.client.post(add, {"title": "Bad", "kind": "manual", "order": 0, "file": bad})
        self.assertFalse(Download.objects.filter(title="Bad").exists())

        self.client.post(add, {"title": "Brochure", "kind": "brochure", "order": 0, "is_published": "on", "file": self.pdf("b.pdf")})
        item = Download.objects.get(title="Brochure")
        path = item.file.path
        self.assertTrue(os.path.exists(path))
        self.assertContains(self.client.get(reverse("admin_dashboard:downloads_overview")), "Brochure")

        # Swapping the file for a link removes the old upload.
        self.client.post(reverse("admin_dashboard:download_edit", args=[item.pk]), {
            "title": "Brochure", "kind": "brochure", "order": 0, "is_published": "on",
            "file-clear": "on", "external_url": "https://example.com/brochure"})
        item.refresh_from_db()
        self.assertTrue(item.is_external)
        self.assertFalse(os.path.exists(path))

        self.client.post(reverse("admin_dashboard:download_toggle_publish", args=[item.pk]))
        item.refresh_from_db()
        self.assertFalse(item.is_published)
        self.client.post(reverse("admin_dashboard:download_delete", args=[item.pk]))
        self.assertFalse(Download.objects.filter(pk=item.pk).exists())

    def test_support_page_and_sitemap_link_the_centre(self):
        self.assertContains(self.client.get(reverse("support_page")), reverse("download_list"))
        self.assertIn(reverse("download_list"), self.client.get("/sitemap.xml").content.decode())
