import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Project, ProjectImage

MEDIA = tempfile.mkdtemp(prefix="test-media-")


def png(name="photo.png", size=(40, 30)):
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 120, 0)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def make_project(**kwargs):
    defaults = dict(title="Shop system", site_type="shop", location="Perambra", summary="Eight cameras for a shop.",
                    cover_image=png(), is_published=True)
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


def tearDownModule():
    shutil.rmtree(MEDIA, ignore_errors=True)


@override_settings(MEDIA_ROOT=MEDIA)
class ProjectPublicTests(TestCase):
    def test_slug_is_unique(self):
        a, b = make_project(title="Villa CCTV"), make_project(title="Villa CCTV")
        self.assertEqual(a.slug, "villa-cctv")
        self.assertEqual(b.slug, "villa-cctv-2")

    def test_list_shows_only_published_and_filters(self):
        make_project(title="Published shop")
        make_project(title="Published school", site_type="school")
        make_project(title="Draft villa", site_type="home", is_published=False)
        r = self.client.get(reverse("project_list"))
        self.assertContains(r, "Published shop")
        self.assertNotContains(r, "Draft villa")
        self.assertEqual([v for v, _ in r.context["filters"]], ["shop", "school"])  # no filter for draft-only types
        r = self.client.get(reverse("project_list"), {"type": "school"})
        self.assertContains(r, "Published school")
        self.assertNotContains(r, "Published shop")

    def test_empty_gallery_message(self):
        self.assertContains(self.client.get(reverse("project_list")), "being updated")

    def test_draft_hidden_from_public_but_previewable_by_staff(self):
        draft = make_project(title="Secret draft", is_published=False)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        self.client.force_login(User.objects.create_user("staff", password="x", is_staff=True))
        r = self.client.get(draft.get_absolute_url())
        self.assertContains(r, "Draft preview")
        self.assertContains(r, "noindex, nofollow")

    def test_detail_page_content(self):
        p = make_project(title="Factory yard", site_type="factory", cameras_installed=12,
                         system_details="12 x 4MP bullet\n- 16-ch NVR\n\n", testimonial="Clear footage at night.",
                         testimonial_author="Plant manager")
        ProjectImage.objects.create(project=p, image=png(), caption="Gate camera")
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "Factory yard")
        self.assertContains(r, "16-ch NVR")
        self.assertContains(r, "Gate camera")
        self.assertContains(r, "Plant manager")
        self.assertContains(r, "site_type=factory")
        self.assertEqual(p.system_lines, ["12 x 4MP bullet", "16-ch NVR"])

    def test_homepage_features_projects_and_sitemap_lists_them(self):
        make_project(title="Featured villa", site_type="home", is_featured=True)
        make_project(title="Unfeatured shop")
        home = self.client.get(reverse("product_list"))
        self.assertContains(home, "Recent projects")
        self.assertContains(home, "Featured villa")
        self.assertNotContains(home, "Unfeatured shop")
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/projects/featured-villa/", sitemap)
        self.assertIn("/projects/unfeatured-shop/", sitemap)

    def test_builder_preselects_site_type_without_jumping_to_a_plan(self):
        r = self.client.get(reverse("system_builder"), {"site_type": "shop"})
        self.assertIsNone(r.context["plan"])
        self.assertContains(r, 'value="shop" checked')


@override_settings(MEDIA_ROOT=MEDIA)
class ProjectAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", password="x", is_staff=True))

    def form_data(self, **overrides):
        data = {"title": "New villa install", "site_type": "home", "location": "Vadakara", "summary": "Six cameras.",
                "order": 0, "is_published": "on"}
        data.update(overrides)
        return data

    def test_requires_staff(self):
        self.client.logout()
        self.client.force_login(User.objects.create_user("customer", password="x"))
        self.assertNotEqual(self.client.get(reverse("admin_dashboard:projects_overview")).status_code, 200)

    def test_create_with_cover_and_gallery_photos(self):
        r = self.client.post(reverse("admin_dashboard:project_add"),
                             {**self.form_data(), "cover_image": png("cover.png"),
                              "gallery_images": [png("a.png"), png("b.png")]})
        self.assertRedirects(r, reverse("admin_dashboard:projects_overview"))
        p = Project.objects.get()
        self.assertTrue(p.is_published)
        self.assertEqual(p.images.count(), 2)
        self.assertEqual(list(p.images.values_list("order", flat=True)), [1, 2])
        self.assertContains(self.client.get(reverse("admin_dashboard:projects_overview")), "New villa install")

    def test_cover_required_and_feature_needs_publish(self):
        r = self.client.post(reverse("admin_dashboard:project_add"), self.form_data())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors.get("cover_image"))
        r = self.client.post(reverse("admin_dashboard:project_add"),
                             {**self.form_data(is_featured="on"), "cover_image": png()} | {"is_published": ""})
        self.assertIn("is_featured", r.context["form"].errors)
        self.assertFalse(Project.objects.exists())

    def test_edit_keeps_cover_updates_captions_removes_and_skips_bad_photos(self):
        p = make_project()
        keep = ProjectImage.objects.create(project=p, image=png(), order=1)
        drop = ProjectImage.objects.create(project=p, image=png(), order=2)
        cover_name = p.cover_image.name
        bad = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        r = self.client.post(reverse("admin_dashboard:project_edit", args=[p.id]), {
            **self.form_data(title="Renamed"), f"caption_{keep.id}": "Front gate", f"order_{keep.id}": "5",
            "delete_image": [str(drop.id)], "gallery_images": [png("new.png"), bad], "save_continue": "1"}, follow=True)
        p.refresh_from_db()
        keep.refresh_from_db()
        self.assertEqual(p.title, "Renamed")
        self.assertEqual(p.cover_image.name, cover_name)
        self.assertEqual((keep.caption, keep.order), ("Front gate", 5))
        self.assertFalse(ProjectImage.objects.filter(id=drop.id).exists())
        self.assertEqual(p.images.count(), 2)  # kept + new; the invalid file was skipped
        self.assertContains(r, "not a valid image")
        self.assertEqual(r.redirect_chain[-1][0], reverse("admin_dashboard:project_edit", args=[p.id]))

    def test_toggle_publish_unfeatures_and_delete_removes(self):
        p = make_project(is_featured=True)
        self.client.post(reverse("admin_dashboard:project_toggle_publish", args=[p.id]))
        p.refresh_from_db()
        self.assertEqual((p.is_published, p.is_featured), (False, False))
        self.client.post(reverse("admin_dashboard:project_delete", args=[p.id]))
        self.assertFalse(Project.objects.exists())
        self.assertEqual(self.client.get(reverse("admin_dashboard:project_delete", args=[p.id])).status_code, 405)

    def test_overview_respects_display_order(self):
        make_project(title="Second", order=2)
        make_project(title="First", order=1)
        r = self.client.get(reverse("admin_dashboard:projects_overview"))
        self.assertEqual([p.title for p in r.context["projects"]], ["First", "Second"])


class DashboardAbandonedCartTests(TestCase):
    def test_dashboard_counts_carts_from_session_payloads(self):
        from django.contrib.sessions.backends.db import SessionStore
        cart_session = SessionStore()
        cart_session["cart"] = {"7": {"price": "1500.00", "quantity": 2}}
        cart_session.create()
        SessionStore().create()  # a session without a cart is ignored
        self.client.force_login(User.objects.create_user("boss", password="x", is_staff=True))
        r = self.client.get(reverse("admin_dashboard:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["abandoned_carts_count"], 1)
        self.assertEqual(str(r.context["abandoned_revenue_potential"]), "3000.00")
