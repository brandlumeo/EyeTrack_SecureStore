from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .tools import CameraGroup, dori_level, lens_estimate, recommend_hdd, recommend_system, storage_estimate


class StorageEstimateTests(SimpleTestCase):
    def test_4mp_h265_continuous(self):
        # 4 Mbps * 86400 s / 8 = 43.2 GB per camera per day
        r = storage_estimate([CameraGroup(4, "4MP")], days=30)
        self.assertEqual(r["lines"][0]["gb_per_day_each"], 43.2)
        self.assertEqual(r["total_gb"], 5184.0)
        self.assertEqual(r["bandwidth_mbps"], 16.0)
        self.assertEqual(r["hdd"], {"drives": 1, "size_tb": 6, "total_tb": 6})  # 5.18 TB + 10% headroom

    def test_h264_fps_hours_and_motion_scale_storage(self):
        base = storage_estimate([CameraGroup(1, "2MP")], days=1, codec="h264")["total_gb"]
        self.assertEqual(base, 43.2)  # 4 Mbps
        self.assertAlmostEqual(storage_estimate([CameraGroup(1, "2MP")], days=1, codec="h264", fps=10)["total_gb"], base * 0.4, places=1)
        self.assertAlmostEqual(storage_estimate([CameraGroup(1, "2MP")], days=1, codec="h264", hours_per_day=12)["total_gb"], base / 2, places=1)
        self.assertAlmostEqual(storage_estimate([CameraGroup(1, "2MP")], days=1, codec="h264", activity_pct=30)["total_gb"], base * 0.3, places=1)

    def test_mixed_groups_and_empty(self):
        r = storage_estimate([CameraGroup(2, "4MP"), CameraGroup(3, "2MP"), CameraGroup(0, "8MP")], days=7)
        self.assertEqual(r["cameras"], 5)
        self.assertEqual(len(r["lines"]), 2)
        self.assertIsNone(storage_estimate([CameraGroup(0, "4MP")], days=7)["hdd"])

    def test_hdd_rounds_up_and_splits_large_requirements(self):
        self.assertEqual(recommend_hdd(0.5)["size_tb"], 1)
        self.assertEqual(recommend_hdd(0.95)["size_tb"], 2)  # 0.95 * 1.1 > 1 TB
        self.assertEqual(recommend_hdd(30), {"drives": 3, "size_tb": 16, "total_tb": 48})


class LensEstimateTests(SimpleTestCase):
    def test_focal_length_and_suggestion(self):
        # 5.6 mm sensor * 10 m / 6 m = 9.33 mm -> next-wider standard lens is 8 mm
        r = lens_estimate(10, 6, '1/2.8"', "4MP")
        self.assertEqual(r["focal_mm"], 9.3)
        self.assertIn("8 mm", r["suggestion"])
        self.assertEqual(r["pixels_per_m"], 427)  # 2560 px / 6 m
        self.assertEqual(r["dori"]["name"], "Identify")
        self.assertEqual([o["lens_mm"] for o in r["options"]], ["2.8", "3.6", "4", "6", "8", "12"])

    def test_extremes(self):
        self.assertIn("PTZ", lens_estimate(50, 5)["suggestion"])
        self.assertIn("wider", lens_estimate(2, 10)["suggestion"])

    def test_dori_thresholds(self):
        self.assertEqual(dori_level(250)["name"], "Identify")
        self.assertEqual(dori_level(249)["name"], "Recognise")
        self.assertEqual(dori_level(62)["name"], "Observe")
        self.assertEqual(dori_level(25)["name"], "Detect")
        self.assertEqual(dori_level(10)["name"], "Below detect")


class RecommendSystemTests(SimpleTestCase):
    def test_small_home_gets_value_dvr_and_starter_package(self):
        plan = recommend_system("home", outdoor=1, indoor=1)
        self.assertEqual(plan["tech_key"], "hd")
        self.assertEqual(plan["recorder_channels"], 4)
        self.assertEqual(plan["package"], "2-Camera Home Kit")
        self.assertEqual(plan["quote_camera_count"], "1-4")
        self.assertEqual(plan["camera_types"], ["dome", "turret"])

    def test_business_or_large_or_audio_gets_ip(self):
        self.assertEqual(recommend_system("office", 2, 2)["tech_key"], "ip")
        self.assertEqual(recommend_system("home", 6, 4)["tech_key"], "ip")
        self.assertEqual(recommend_system("home", 1, 1, audio=True)["tech_key"], "ip")

    def test_factory_large_outdoor(self):
        plan = recommend_system("factory", outdoor=10, indoor=4, night="colour")
        self.assertEqual(plan["recorder_channels"], 16)
        self.assertEqual(plan["package"], "16+ Camera IP System")
        self.assertEqual(plan["quote_camera_count"], "9-16")
        self.assertIn("bullet", plan["camera_types"])
        self.assertTrue(any("PTZ" in tip for tip in plan["tips"]))

    def test_wireless_and_zero(self):
        self.assertEqual(recommend_system("apartment", 1, 2, cabling="wireless")["camera_types"], ["wireless"])
        self.assertIsNone(recommend_system("home", 0, 0))


class ToolsViewTests(TestCase):
    def test_pages_render(self):
        for name in ["tools_hub", "system_builder", "storage_calculator", "lens_calculator", "camera_guide"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_calculator_pages_show_default_result(self):
        self.assertContains(self.client.get(reverse("storage_calculator")), "1 &times; 6 TB")
        self.assertContains(self.client.get(reverse("lens_calculator")), "9.3")

    def test_storage_api(self):
        r = self.client.get(reverse("storage_api"), {"cameras": 8, "resolution": "2MP", "days": 15})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["result"]["total_gb"], 2592.0)  # 8 * 21.6 GB * 15 days
        bad = self.client.get(reverse("storage_api"), {"cameras": 0})
        self.assertEqual(bad.status_code, 400)
        self.assertIn("cameras", bad.json()["errors"])

    def test_lens_api_rejects_bad_input(self):
        self.assertEqual(self.client.get(reverse("lens_api"), {"distance": "abc"}).status_code, 400)
        self.assertEqual(self.client.get(reverse("lens_api"), {"distance": 20, "width": 4}).json()["result"]["focal_mm"], 28.0)

    def test_builder_plan_and_quote_prefill(self):
        r = self.client.get(reverse("system_builder"), {
            "site_type": "shop", "outdoor": 2, "indoor": 4, "night": "ir", "audio": "no", "days": 30, "cabling": "yes"})
        self.assertContains(r, "Your recommended system")
        plan = r.context["plan"]
        self.assertEqual(plan["package"], "8-Camera Business Kit")
        query = parse_qs(urlparse(r.context["quote_url"]).query)
        self.assertEqual(query["camera_count"], ["5-8"])
        self.assertEqual(query["package"], ["8-Camera Business Kit"])
        quote_page = self.client.get(r.context["quote_url"])
        self.assertContains(quote_page, "System builder plan: 6 cameras")
        self.assertContains(quote_page, 'value="shop" selected')

    def test_builder_requires_a_camera(self):
        r = self.client.get(reverse("system_builder"), {"site_type": "home", "outdoor": 0, "indoor": 0})
        self.assertIsNone(r.context["plan"])
        self.assertContains(r, "Add at least one camera point")
