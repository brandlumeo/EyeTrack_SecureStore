import json
from django.contrib.auth.models import User
from django.core import mail
from django.test import RequestFactory, TestCase
from decimal import Decimal
from django.urls import reverse

from accounts.models import Address
from orders.models import Invoice, Order, Payment, Shipment
from .models import CameraSpecification, Category, Product, ServiceableArea
from .views import _build_compare_specs, _build_product_specs, quick_view_product


class StoreFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Camera",
            description="Demo camera",
            price="1000.00",
            stock=1,
            is_available=True,
            image="products/test.jpg",
        )
        self.user = User.objects.create_user(username="buyer", email="buyer@example.com", password="StrongPass123!")
        ServiceableArea.objects.create(pincode="673001", delivery_available=True)

    def checkout_data(self, **overrides):
        """A complete manual checkout submission (structured address, serviceable pincode)."""
        data = {
            "full_name": "Buyer Test",
            "email": "buyer@example.com",
            "phone": "9999999999",
            "addr_house": "12 Rose Villa",
            "addr_street": "MG Road",
            "addr_city": "Kozhikode",
            "addr_state": "Kerala",
            "addr_pincode": "673001",
        }
        data.update(overrides)
        return data

    def save_address(self):
        return Address.objects.create(
            user=self.user,
            full_name="Saved Buyer",
            phone_number="8888888888",
            house_street="221B Baker Street",
            city="Kozhikode",
            state="Kerala",
            pincode="673001",
            country="India",
            is_default=True,
        )

    def test_add_to_cart_requires_post(self):
        response = self.client.get(reverse("add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_respects_stock_limit(self):
        self.client.post(reverse("add_to_cart", args=[self.product.id]))
        self.client.post(reverse("add_to_cart", args=[self.product.id]))
        session = self.client.session
        self.assertEqual(session["cart"][str(self.product.id)], 1)

    def test_add_to_cart_with_quantity(self):
        # Reset stock for this test
        self.product.stock = 10
        self.product.save()
        
        # Post with quantity 3
        response = self.client.post(reverse("add_to_cart", args=[self.product.id]), {'quantity': 3})
        session = self.client.session
        self.assertEqual(session["cart"][str(self.product.id)], 3)
        
        # Post again with quantity 2
        self.client.post(reverse("add_to_cart", args=[self.product.id]), {'quantity': 2})
        session = self.client.session
        self.assertEqual(session["cart"][str(self.product.id)], 5)
        
        # Post with too much
        response = self.client.post(reverse("add_to_cart", args=[self.product.id]), {'quantity': 6})
        session = self.client.session
        self.assertEqual(session["cart"][str(self.product.id)], 5) # Still 5

    def test_checkout_prevents_order_when_stock_insufficient(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()
        self.client.login(username="buyer", password="StrongPass123!")

        response = self.client.post(reverse("checkout"), data=self.checkout_data())

        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_prefills_default_saved_address(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()
        address = self.save_address()

        response = self.client.get(reverse("checkout"))

        self.assertContains(response, 'id="checkoutSavedAddress"', html=False)
        self.assertContains(response, 'value="Saved Buyer"', html=False)
        self.assertContains(response, "221B Baker Street, Kozhikode, Kerala 673001, India")
        # each option carries its real address data, so the page can show and validate it
        self.assertContains(response, 'data-pincode="673001"', html=False)
        # the default address is preselected, so the manual fields start collapsed and disabled
        self.assertContains(response, 'id="manualAddressFields" disabled hidden', html=False)
        self.assertEqual(response.context["selected_address_id"], str(address.id))

    def test_checkout_can_use_saved_address_selection(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()
        address = self.save_address()

        response = self.client.post(
            reverse("checkout"),
            data={
                "saved_address": str(address.id),
                "full_name": "",
                "email": "",
                "phone": "",
            },
        )

        order = Order.objects.get()
        self.assertRedirects(response, reverse("razorpay_checkout", args=[order.id]), fetch_redirect_response=False)
        self.assertEqual(order.full_name, "Saved Buyer")
        self.assertEqual(order.email, "buyer@example.com")
        self.assertEqual(order.phone, "8888888888")
        self.assertEqual(order.address, "221B Baker Street, Kozhikode, Kerala 673001, India")

    def test_manual_address_overrides_selected_saved_address(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()
        address = self.save_address()

        self.client.post(reverse("checkout"), data=self.checkout_data(saved_address=str(address.id)))

        order = Order.objects.get()
        self.assertEqual(order.address, "12 Rose Villa\nMG Road\nKozhikode, Kerala - 673001")

    def test_checkout_rejects_unserviceable_pincode(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        response = self.client.post(reverse("checkout"), data=self.checkout_data(addr_pincode="110001"))

        self.assertRedirects(response, reverse("checkout"), fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(), 0)

    def test_simulated_payment_reduces_stock_and_confirms_order(self):
        self.client.login(username="buyer", password="StrongPass123!")
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        with self.captureOnCommitCallbacks(execute=True):
            checkout_response = self.client.post(reverse("checkout"), data=self.checkout_data())
        order = Order.objects.get()
        # Note: payment_method default is ONLINE, redirects to razorpay_checkout
        self.assertRedirects(checkout_response, reverse("razorpay_checkout", args=[order.id]), fetch_redirect_response=False)
        self.assertEqual(order.order_status, Order.OrderStatus.PENDING)

class ProductSpecMappingTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.vdp_category = Category.objects.create(name="Video Door Phones", slug="homegate-automation")
        self.cctv_category = Category.objects.create(name="CCTV Cameras", slug="cctv-installation")

    def test_quick_view_returns_compare_ready_video_door_phone_specs(self):
        product = Product.objects.create(
            category=self.vdp_category,
            name="Lobby VDP",
            description="Video door phone",
            price="7200.00",
            stock=5,
            is_available=True,
            screen_size="7 inch LCD Touch Display",
            camera_resolution="2MP HD",
            night_vision=True,
            connectivity_type="wifi",
            unlock_method="app",
            audio_communication=True,
            mobile_app_support=True,
            storage_support_vdp="microSD Card / Cloud Storage",
            power_source_vdp="dc12v",
            installation_type="surface",
            warranty_vdp="2 Years",
        )

        request = self.factory.get(reverse("quick_view_product", args=[product.id]))
        response = quick_view_product(request, product.id)
        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.content)
        specs = payload["product"]["specs"]
        self.assertEqual(specs["screen_size"], "7 inch LCD Touch Display")
        self.assertEqual(specs["camera_resolution"], "2MP HD")
        self.assertEqual(specs["night_vision"], "Yes")
        self.assertEqual(specs["connectivity_type"], "Wi-Fi")
        self.assertEqual(specs["unlock_method"], "Mobile App")
        self.assertEqual(specs["audio_communication"], "Yes")
        self.assertEqual(specs["mobile_app_support"], "Yes")
        self.assertEqual(specs["storage_support"], "microSD Card / Cloud Storage")
        self.assertEqual(specs["power_source"], "DC 12V")
        self.assertEqual(specs["installation_type"], "Surface Mount")
        self.assertEqual(specs["warranty"], "2 Years")

    def test_product_detail_specs_keep_human_readable_video_door_phone_labels(self):
        product = Product.objects.create(
            category=self.vdp_category,
            name="Gate VDP",
            description="Video door phone",
            price="8500.00",
            stock=4,
            is_available=True,
            screen_size="7 inch TFT LCD",
            camera_resolution="2MP HD",
            night_vision=True,
            connectivity_type="wired",
            unlock_method="hybrid",
            audio_communication=True,
            mobile_app_support=False,
            storage_support_vdp="Local Storage / NVR",
            power_source_vdp="dc12v",
            installation_type="surface",
            warranty_vdp="2 Years",
        )

        specs = _build_product_specs(product)
        # Convert list of dicts to a dict for easier testing
        specs_dict = {s['label']: s['value'] for s in specs}
        self.assertEqual(specs_dict["Screen Size"], "7 inch TFT LCD")
        self.assertEqual(specs_dict["Camera Resolution"], "2MP HD")
        self.assertEqual(specs_dict["Connectivity"], "Wired")
        self.assertEqual(specs_dict["Unlock Method"], "Multiple Methods")
        self.assertEqual(specs_dict["Two-Way Audio"], "Yes")
        self.assertEqual(specs_dict["Mobile App"], "No")

    def test_cctv_product_fields_take_priority_over_legacy_related_spec_model(self):
        product = Product.objects.create(
            category=self.cctv_category,
            name="Warehouse Camera",
            description="CCTV camera",
            price="4999.00",
            stock=6,
            is_available=True,
            camera_type="bullet",
            resolution="8MP",
            night_vision_range="50 m",
            field_of_view="110deg",
            lens="3.6mm",
            frame_rate="30fps",
            weatherproof="IP67",
            connectivity="wifi",
            power_source="poe",
            storage_support="NVR / microSD",
            audio_support=False,
            ai_detection=True,
            warranty="3 Years",
        )
        CameraSpecification.objects.create(
            product=product,
            camera_type="dome",
            resolution_mp="2.0",
            night_vision_range_m=20,
            field_of_view_deg=90,
            lens_mm="2.8",
            frame_rate_fps=15,
            weatherproof_rating="IP66",
            connectivity="wired",
            power_source="dc12v",
            storage_support="Cloud",
            audio_support=True,
            ai_detection=False,
            warranty_years=1,
        )

        compare_specs = _build_compare_specs(product)
        detail_specs_list = _build_product_specs(product)
        detail_specs = {s['label']: s['value'] for s in detail_specs_list}

        self.assertEqual(compare_specs["camera_type"], "Bullet")
        self.assertEqual(compare_specs["resolution_mp"], "8MP")
        self.assertEqual(compare_specs["connectivity"], "Wi-Fi")
        self.assertEqual(compare_specs["audio_support"], "No")
        self.assertEqual(compare_specs["ai_detection"], "Yes")
        self.assertEqual(compare_specs["warranty_years"], "3 Years")
        self.assertEqual(detail_specs["Resolution"], "8MP")
        self.assertEqual(detail_specs["Connectivity"], "Wi-Fi")
