import io
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import Notification, Profile
from orders.models import Order, Technician

from .models import ServiceTicket

MEDIA = tempfile.mkdtemp(prefix="test-ticket-media-")


def tearDownModule():
    shutil.rmtree(MEDIA, ignore_errors=True)


def png(name="photo.png"):
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (10, 120, 200)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA, ADMINS=[("Admin", "admin@example.com")])
@patch("support.tickets._send_async")
class ServiceTicketTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user("cust", email="cust@example.com", password="StrongPass123!", first_name="Asha")
        Profile.objects.create(user=self.customer, phone_number="9876543210")
        self.other = User.objects.create_user("other", email="other@example.com", password="StrongPass123!")
        self.staff = User.objects.create_user("staff", email="staff@example.com", password="StrongPass123!", is_staff=True)
        self.order = Order.objects.create(user=self.customer, full_name="Asha", email="cust@example.com", phone="9876543210",
                                          address="Kozhikode", total="1000.00")
        self.other_order = Order.objects.create(user=self.other, full_name="O", email="other@example.com", phone="9000000000",
                                                address="X", total="10.00")

    def login(self, user):
        self.client.login(username=user.username, password="StrongPass123!")

    def create(self, **overrides):
        data = {"category": "camera_offline", "subject": "Gate camera offline", "description": "No video since yesterday.",
                "contact_phone": "9876543210", "site_location": "Perambra", "order": self.order.pk}
        data.update(overrides)
        return self.client.post(reverse("ticket_create"), data)

    def test_customer_pages_need_login(self, send):
        self.assertRedirects(self.client.get(reverse("ticket_list")), reverse("login") + "?next=" + reverse("ticket_list"))

    def test_create_with_photos_prefill_and_staff_notification(self, send):
        self.login(self.customer)
        page = self.client.get(reverse("ticket_create"), {"order": self.order.pk})
        self.assertEqual(page.context["form"].initial["order"], self.order.pk)
        self.assertEqual(page.context["form"].initial["contact_phone"], "9876543210")
        # someone else's order is never offered or prefilled
        self.assertNotIn("order", self.client.get(reverse("ticket_create"), {"order": self.other_order.pk}).context["form"].initial)

        response = self.client.post(reverse("ticket_create"), {
            "category": "recording", "subject": "No recording", "description": "Playback is empty.",
            "contact_phone": "9876543210", "order": self.order.pk, "photos": [png("a.png"), png("b.png")]})
        ticket = ServiceTicket.objects.get()
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual((ticket.user, ticket.order, ticket.status), (self.customer, self.order, "open"))
        self.assertEqual(ticket.attachments.count(), 2)
        self.assertEqual(ticket.reference, "SR-%05d" % ticket.pk)
        self.assertTrue(Notification.objects.filter(user=self.staff, title="New service request").exists())
        self.assertEqual(send.call_args.args[2], ["admin@example.com"])

    def test_cannot_attach_someone_elses_order(self, send):
        self.login(self.customer)
        response = self.create(order=self.other_order.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn("order", response.context["form"].errors)
        self.assertFalse(ServiceTicket.objects.exists())

    def test_invalid_photo_is_skipped_but_ticket_saved(self, send):
        self.login(self.customer)
        bad = SimpleUploadedFile("x.png", b"not an image", content_type="image/png")
        response = self.client.post(reverse("ticket_create"), {
            "category": "other", "subject": "Hi", "description": "Help", "contact_phone": "9876543210", "photos": [bad]}, follow=True)
        self.assertEqual(ServiceTicket.objects.get().attachments.count(), 0)
        self.assertContains(response, "not a valid image")

    def test_customers_only_see_their_own_tickets(self, send):
        self.login(self.customer)
        self.create()
        ticket = ServiceTicket.objects.get()
        self.client.logout()
        self.login(self.other)
        self.assertEqual(self.client.get(reverse("ticket_detail", args=[ticket.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("ticket_list")), "Gate camera offline")

    def test_customer_reply_reopens_and_notifies_staff(self, send):
        self.login(self.customer)
        self.create()
        ticket = ServiceTicket.objects.get()
        ticket.status = "waiting_customer"
        ticket.save()
        self.client.post(reverse("ticket_detail", args=[ticket.pk]), {"body": "Here is the model number."})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "open")
        self.assertEqual(ticket.messages.get().from_staff, False)
        self.assertTrue(Notification.objects.filter(user=self.staff, title="Customer replied").exists())

    def test_close_then_no_more_replies(self, send):
        self.login(self.customer)
        self.create()
        ticket = ServiceTicket.objects.get()
        self.client.post(reverse("ticket_close", args=[ticket.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "closed")
        self.assertIsNotNone(ticket.closed_at)
        self.client.post(reverse("ticket_detail", args=[ticket.pk]), {"body": "one more thing"})
        self.assertEqual(ticket.messages.count(), 0)

    def test_staff_pages_need_staff(self, send):
        self.login(self.customer)
        self.assertNotEqual(self.client.get(reverse("admin_dashboard:tickets_overview")).status_code, 200)

    def test_staff_reply_status_and_assignment_notify_customer(self, send):
        self.login(self.customer)
        self.create()
        ticket = ServiceTicket.objects.get()
        tech = Technician.objects.create(name="Ravi", phone="9111111111")
        self.client.logout()
        self.login(self.staff)

        overview = self.client.get(reverse("admin_dashboard:tickets_overview"), {"search": ticket.reference})
        self.assertContains(overview, "Gate camera offline")
        page = self.client.get(reverse("admin_dashboard:ticket_manage", args=[ticket.pk]))
        self.assertContains(page, "No video since yesterday.")

        self.client.post(reverse("admin_dashboard:ticket_manage", args=[ticket.pk]), {
            "body": "We'll visit on Friday.", "status": "visit_scheduled", "priority": "urgent",
            "assigned_technician": tech.pk, "visit_date": "2026-11-13"})
        ticket.refresh_from_db()
        self.assertEqual((ticket.status, ticket.priority, ticket.assigned_technician, str(ticket.visit_date)),
                         ("visit_scheduled", "urgent", tech, "2026-11-13"))
        msg = ticket.messages.get()
        self.assertTrue(msg.from_staff)
        note = Notification.objects.get(user=self.customer, title="Update on your service request")
        self.assertIn("We'll visit on Friday.", note.message)
        self.assertIn("Visit date: Fri, 13 Nov 2026", note.message)
        self.assertEqual(send.call_args.args[2], ["cust@example.com"])

        # customer sees the staff reply and visit details
        self.client.logout()
        self.login(self.customer)
        detail = self.client.get(reverse("ticket_detail", args=[ticket.pk]))
        self.assertContains(detail, "Eyetrack Support")
        self.assertContains(detail, "Ravi")

    def test_staff_close_sets_closed_at_and_silent_update_does_not_notify(self, send):
        self.login(self.customer)
        self.create()
        ticket = ServiceTicket.objects.get()
        self.client.logout()
        self.login(self.staff)
        # priority-only change: no reply, no status change -> no customer notification
        self.client.post(reverse("admin_dashboard:ticket_manage", args=[ticket.pk]), {"status": "open", "priority": "urgent"})
        self.assertFalse(Notification.objects.filter(user=self.customer).exists())
        self.client.post(reverse("admin_dashboard:ticket_manage", args=[ticket.pk]), {"status": "closed", "priority": "urgent"})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "closed")
        self.assertIsNotNone(ticket.closed_at)
        self.assertTrue(Notification.objects.filter(user=self.customer).exists())

    def test_entry_points_link_to_service_requests(self, send):
        self.login(self.customer)
        self.assertContains(self.client.get(reverse("order_tracking", args=[self.order.pk])),
                            reverse("ticket_create") + "?order=%d" % self.order.pk)
        self.assertContains(self.client.get(reverse("account_dashboard")), reverse("ticket_list"))
        self.assertContains(self.client.get(reverse("support_page")), reverse("ticket_create"))
