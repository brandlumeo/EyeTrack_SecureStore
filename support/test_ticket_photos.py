import io
import os
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import ServiceTicket, TicketAttachment

PUBLIC = tempfile.mkdtemp(prefix="test-public-media-")
PRIVATE = tempfile.mkdtemp(prefix="test-private-media-")


def tearDownModule():
    shutil.rmtree(PUBLIC, ignore_errors=True)
    shutil.rmtree(PRIVATE, ignore_errors=True)


def png():
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (200, 30, 30)).save(buf, "PNG")
    return SimpleUploadedFile("gate.png", buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=PUBLIC, PRIVATE_MEDIA_ROOT=PRIVATE)
@patch("support.tickets._send_async")
class TicketPhotoPrivacyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="StrongPass123!")
        self.other = User.objects.create_user("other", password="StrongPass123!")
        self.staff = User.objects.create_user("staff", password="StrongPass123!", is_staff=True)
        self.client.login(username="owner", password="StrongPass123!")
        self.client.post(reverse("ticket_create"), {
            "category": "camera_offline", "subject": "Gate camera", "description": "Offline", "contact_phone": "9876543210",
            "photos": [png()]})
        self.ticket = ServiceTicket.objects.get(user=self.owner)
        self.photo = TicketAttachment.objects.get(ticket=self.ticket)
        self.url = reverse("ticket_photo", args=[self.photo.pk])
        self.client.logout()

    def drain(self, response):
        return b"".join(response.streaming_content)

    def test_photo_is_stored_outside_public_media(self, send):
        path = self.photo.image.path
        self.assertTrue(path.startswith(os.path.abspath(PRIVATE)))
        self.assertTrue(os.path.exists(path))
        self.assertFalse(any(files for _, _, files in os.walk(PUBLIC)))
        with self.assertRaises(ValueError):
            self.photo.image.url  # no public URL can be produced by mistake
        public_try = "/media/" + self.photo.image.name
        self.assertEqual(self.client.get(public_try).status_code, 404)

    def test_only_owner_and_staff_can_open_it(self, send):
        anon = self.client.get(self.url)
        self.assertEqual(anon.status_code, 302)
        self.assertIn(reverse("login"), anon["Location"])

        self.client.login(username="other", password="StrongPass123!")
        self.assertEqual(self.client.get(self.url).status_code, 404)

        for user in ("owner", "staff"):
            self.client.login(username=user, password="StrongPass123!")
            r = self.client.get(self.url)
            self.assertEqual(r.status_code, 200, user)
            self.assertTrue(self.drain(r).startswith(b"\x89PNG"))
            self.assertIn("no-store", r["Cache-Control"])
            self.assertEqual(r["Content-Disposition"], "inline")

    def test_ticket_pages_link_through_the_checked_view(self, send):
        self.client.login(username="owner", password="StrongPass123!")
        page = self.client.get(reverse("ticket_detail", args=[self.ticket.pk])).content.decode()
        self.assertIn(self.url, page)
        self.assertNotIn("/media/service_tickets/", page)
        self.client.login(username="staff", password="StrongPass123!")
        manage = self.client.get(reverse("admin_dashboard:ticket_manage", args=[self.ticket.pk])).content.decode()
        self.assertIn(self.url, manage)
        self.assertNotIn("/media/service_tickets/", manage)
