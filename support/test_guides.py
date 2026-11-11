from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ServiceTicket, ViewingGuide


class ViewingGuideTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.customer = User.objects.create_user("cust", email="c@example.com", password="x")

    def test_starter_guides_arrive_as_unpublished_drafts(self):
        drafts = ViewingGuide.objects.all()
        self.assertEqual(sorted(g.brand for g in drafts), ["CP Plus", "Dahua", "General", "Hikvision"])
        self.assertFalse(any(g.is_published for g in drafts))
        self.assertTrue(all(not g.android_url and not g.ios_url for g in drafts))  # links left for staff to paste

    def test_drafts_are_hidden_from_the_public_but_previewable_by_staff(self):
        draft = ViewingGuide.objects.get(brand="Hikvision")
        listing = self.client.get(reverse("guide_list"))
        self.assertContains(listing, "being prepared")
        self.assertNotContains(listing, draft.title)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        self.client.force_login(self.staff)
        preview = self.client.get(draft.get_absolute_url())
        self.assertContains(preview, "Draft preview")
        self.assertContains(preview, "noindex, nofollow")

    def test_published_guide_page_list_filter_and_sitemap(self):
        hik = ViewingGuide.objects.get(brand="Hikvision")
        general = ViewingGuide.objects.get(brand="General")
        ViewingGuide.objects.filter(pk__in=[hik.pk, general.pk]).update(is_published=True, android_url="https://play.google.com/store/apps/details?id=example")
        page = self.client.get(hik.get_absolute_url())
        self.assertContains(page, "Scan QR Code")                      # a step
        self.assertContains(page, "Device offline in the app")         # a troubleshooting problem
        self.assertContains(page, "Google Play")                       # app link shown once set
        self.assertNotContains(page, "App Store")                      # not set -> not shown
        listing = self.client.get(reverse("guide_list"), {"brand": "Hikvision"})
        self.assertContains(listing, hik.title)
        self.assertContains(listing, general.title)                    # general guide shown with every brand
        self.assertNotContains(listing, "Dahua: view cameras")         # still a draft
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(hik.get_absolute_url(), sitemap)
        self.assertNotIn(ViewingGuide.objects.get(brand="Dahua").get_absolute_url(), sitemap)

    def test_staff_manage_guides(self):
        self.client.force_login(self.customer)
        self.assertNotEqual(self.client.get(reverse("admin_dashboard:guides_overview")).status_code, 200)
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("admin_dashboard:guides_overview")), "Draft")
        r = self.client.post(reverse("admin_dashboard:guide_add"), {
            "title": "Uniview: EZView", "brand": "Uniview", "app_name": "EZView", "summary": "Add a Uniview NVR.",
            "steps": "Install the app\nAdd the device", "order": 5, "save_preview": "1"})
        guide = ViewingGuide.objects.get(brand="Uniview")
        self.assertRedirects(r, guide.get_absolute_url(), fetch_redirect_response=False)
        self.assertFalse(guide.is_published)
        self.client.post(reverse("admin_dashboard:guide_toggle_publish", args=[guide.pk]))
        guide.refresh_from_db()
        self.assertTrue(guide.is_published)
        self.client.post(reverse("admin_dashboard:guide_delete", args=[guide.pk]))
        self.assertFalse(ViewingGuide.objects.filter(pk=guide.pk).exists())

    @patch("support.tickets._send_async")
    def test_service_request_pages_point_to_guides_once_published(self, send):
        self.client.force_login(self.customer)
        self.assertNotContains(self.client.get(reverse("ticket_create")), reverse("guide_list"))
        ViewingGuide.objects.filter(brand="General").update(is_published=True)
        self.assertContains(self.client.get(reverse("ticket_create")), reverse("guide_list"))
        ticket = ServiceTicket.objects.create(user=self.customer, category="mobile_view", subject="App", description="x", contact_phone="9876543210")
        self.assertContains(self.client.get(reverse("ticket_detail", args=[ticket.pk])), "phone viewing guides")
        other = ServiceTicket.objects.create(user=self.customer, category="damage", subject="Cable", description="x", contact_phone="9876543210")
        self.assertNotContains(self.client.get(reverse("ticket_detail", args=[other.pk])), "phone viewing guides")
