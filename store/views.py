from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max, Min, Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

import json

import razorpay

from orders.emails import send_order_invoice_email, send_order_placed_email, send_email_async, send_admin_order_notification_email
from orders.models import Order, OrderItem, Payment, Shipment
from .models import Category, Product, CameraSpecification, Wishlist, Review, ReviewMedia, Coupon, ServiceableArea, StockNotification, ReviewHelpful, Project
from .forms import ReviewForm
from .specs import (
    SPEC_TYPE_BIOMETRIC,
    SPEC_TYPE_CCTV,
    SPEC_TYPE_NETWORK,
    SPEC_TYPE_SMART_LOCK,
    SPEC_TYPE_VIDEO_DOOR_PHONE,
    get_product_spec_type,
)

def live_search(request):
    """API endpoint for live ajax search"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
        
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(category__name__icontains=query) | Q(description__icontains=query),
        is_available=True
    ).select_related('category')[:5]
    
    results = []
    for p in products:
        results.append({
            'name': p.name,
            'url': reverse('product_detail', args=[p.slug]),
            'price': str(p.price),
            'category': p.category.name,
            'image': p.image.url if p.image else ''
        })
    return JsonResponse({'results': results})


def _cart_total_items(cart):
    return sum(cart.values())


def _format_saved_address(address):
    locality_parts = [part.strip() for part in [address.city, address.state] if part and part.strip()]
    locality = ", ".join(locality_parts)
    if address.pincode:
        locality = f"{locality} {address.pincode}".strip() if locality else address.pincode.strip()
    parts = [address.house_street, locality, address.country]
    return ", ".join(part.strip() for part in parts if part and part.strip())


def _build_checkout_form_initial(user, saved_address=None):
    initial = {
        "full_name": "",
        "email": user.email or "",
        "phone": "",
        "address": "",
    }
    if not saved_address:
        return initial

    initial.update(
        {
            "full_name": saved_address.full_name,
            "phone": saved_address.phone_number,
            "address": _format_saved_address(saved_address),
        }
    )
    return initial


def _build_saved_address_option(user, saved_address):
    label = f"{saved_address.full_name} - {saved_address.city}, {saved_address.state}"
    if saved_address.is_default:
        label = f"{label} (Default)"
    return {
        "id": str(saved_address.id),
        "label": label,
        "full_name": saved_address.full_name,
        "email": user.email or "",
        "phone": saved_address.phone_number,
        "phone_number": saved_address.phone_number,
        "house_street": saved_address.house_street,
        "landmark": saved_address.landmark,
        "city": saved_address.city,
        "state": saved_address.state,
        "pincode": saved_address.pincode,
        "address": _format_saved_address(saved_address),
        "is_default": saved_address.is_default,
    }


def _build_legacy_product_specs(product):
    """Return a dict of human-readable specs for a product based on its category."""
    cat = product.category.name if product.category else ""
    cat_slug = product.category.slug if product.category else ""

    # 1. NEW APPROACH: Check related specification models first
    # This ensures that data added through the new Admin Dashboard takes priority.
    
    # CCTV / Camera Specs
    if 'camera' in cat_slug or 'cctv' in cat_slug or 'video' in cat_slug or 'door' in cat_slug:
        try:
            s = product.camera_specs
            return {
                "Camera Type": s.get_camera_type_display() or "-",
                "Resolution": f"{s.resolution_mp} MP" if s.resolution_mp else "-",
                "Lens": f"{s.lens_mm} mm" if s.lens_mm else "-",
                "Field of View": f"{s.field_of_view_deg}°" if s.field_of_view_deg else "-",
                "Night Vision": f"{s.night_vision_range_m} m" if s.night_vision_range_m else "-",
                "Frame Rate": f"{s.frame_rate_fps} fps" if s.frame_rate_fps else "-",
                "Weatherproof": s.weatherproof_rating or "-",
                "Connectivity": s.get_connectivity_display() if s.connectivity else "-",
                "Power Source": s.get_power_source_display() if s.power_source else "-",
                "Storage Support": s.storage_support or "-",
                "Two-Way Audio": "Yes" if s.audio_support else "No",
                "AI Detection": "Yes" if s.ai_detection else "No",
                "Warranty": f"{s.warranty_years} year(s)" if s.warranty_years else "-",
            }
        except Exception:
            pass

    # Biometric Specs
    elif 'biometric' in cat_slug:
        try:
            s = product.biometric_specs
            return {
                "Authentication Method": s.authentication_method or "-",
                "User Capacity": str(s.user_capacity) if s.user_capacity else "-",
                "Fingerprint Sensor": s.fingerprint_sensor or "-",
                "Face Recognition": "Yes" if s.face_recognition else "No",
                "Card Support": "Yes" if s.card_support else "No",
                "Connectivity": s.connectivity or "-",
                "Power Supply": s.power_supply or "-",
            }
        except Exception:
            pass

    # Smart Lock Specs
    elif 'lock' in cat_slug or 'smart-lock' in cat_slug:
        try:
            s = product.smartlock_specs
            return {
                "Unlock Methods": s.unlock_methods or "-",
                "Connectivity": s.connectivity or "-",
                "Battery Life": s.battery_life or "-",
                "Emergency Unlock": "Yes" if s.emergency_unlock else "No",
            }
        except Exception:
            pass

    # Video Door Phone Specs (Fields are on Product model)
    elif 'homegate' in cat_slug or 'automation' in cat_slug:
        return {
            "Screen Size": product.screen_size or "-",
            "Camera Resolution": product.camera_resolution or "-",
            "Night Vision": "Yes" if product.night_vision else "No",
            "Connectivity": product.get_connectivity_type_display() if product.connectivity_type else "-",
            "Unlock Method": product.get_unlock_method_display() if product.unlock_method else "-",
            "Two-Way Audio": "Yes" if product.audio_communication else "No",
            "Mobile App": "Yes" if product.mobile_app_support else "No",
            "Storage": product.storage_support_vdp or "-",
            "Power Source": product.get_power_source_vdp_display() if product.power_source_vdp else "-",
            "Installation": product.get_installation_type_display() if product.installation_type else "-",
            "Warranty": product.warranty_vdp or "-",
        }

    # Network Specs
    elif 'network' in cat_slug or 'switch' in cat_slug or 'router' in cat_slug or 'consulting' in cat_slug:
        try:
            s = product.network_specs
            return {
                "Ports": str(s.ports) if s.ports else "-",
                "Bandwidth": s.bandwidth or "-",
                "PoE Support": "Yes" if s.poe_support else "No",
            }
        except Exception:
            pass

    # 2. LEGACY / FALLBACK: Check Product model fields directly
    specs = {}
    
    # Only add specs if they are NOT the default/empty values to avoid false-positive matches
    if product.camera_type:
        specs["Camera Type"] = product.get_camera_type_display() or product.camera_type
    if product.resolution:
        specs["Resolution"] = product.resolution
    if product.night_vision_range:
        specs["Night Vision"] = product.night_vision_range
    if product.field_of_view:
        specs["Field of View"] = product.field_of_view
    if product.lens:
        specs["Lens"] = product.lens
    if product.frame_rate:
        specs["Frame Rate"] = product.frame_rate
    if product.weatherproof:
        specs["Weatherproof"] = product.weatherproof
    if product.connectivity:
        specs["Connectivity"] = product.get_connectivity_display() or product.connectivity
    if product.power_source:
        specs["Power Source"] = product.get_power_source_display() or product.power_source
    if product.storage_support:
        specs["Storage Support"] = product.storage_support
    if product.warranty:
        specs["Warranty"] = product.warranty

    # Boolean logic (only if actually relevant or non-default)
    # We use "audio_communication" for Door Phones often
    if product.audio_communication:
         specs["Two-Way Audio"] = "Yes"
    
    # We only add audio/ai if they are True (non-default for audio_support, ai_detection)
    if product.audio_support:
        specs["Audio Support"] = "Yes"
    if product.ai_detection:
        specs["AI Detection"] = "Yes"

    # Video Door Phone specific legacy fields
    if product.screen_size:
        specs["Screen Size"] = product.screen_size
    if product.camera_resolution:
        specs["Camera Resolution"] = product.camera_resolution
    if product.unlock_method:
        specs["Unlock Method"] = product.get_unlock_method_display() or product.unlock_method
    if product.mobile_app_support:
        specs["Mobile App Control"] = "Yes"
    
    return specs


def _has_direct_cctv_specs(product):
    return any(
        [
            product.camera_type,
            product.resolution,
            product.night_vision_range,
            product.field_of_view,
            product.lens,
            product.frame_rate,
            product.weatherproof,
            product.connectivity,
            product.power_source,
            product.storage_support,
            product.warranty,
            product.audio_support,
            product.ai_detection,
        ]
    )


def _build_cctv_compare_specs(product):
    if _has_direct_cctv_specs(product):
        return {
            "camera_type": product.get_camera_type_display() if product.camera_type else "-",
            "resolution_mp": product.resolution or "-",
            "night_vision_range_m": product.night_vision_range or "-",
            "field_of_view_deg": product.field_of_view or "-",
            "lens": product.lens or "-",
            "frame_rate": product.frame_rate or "-",
            "weatherproof": product.weatherproof or "-",
            "connectivity": product.get_connectivity_display() if product.connectivity else "-",
            "power_source": product.get_power_source_display() if product.power_source else "-",
            "storage_support": product.storage_support or "-",
            "audio_support": "Yes" if product.audio_support else "No",
            "ai_detection": "Yes" if product.ai_detection else "No",
            "warranty_years": product.warranty or "-",
        }

    camera_specs = product.camera_specs if hasattr(product, "camera_specs") else None
    if camera_specs:
        return {
            "camera_type": camera_specs.get_camera_type_display() if camera_specs.camera_type else "-",
            "resolution_mp": f"{camera_specs.resolution_mp} MP" if camera_specs.resolution_mp else "-",
            "night_vision_range_m": f"{camera_specs.night_vision_range_m} m" if camera_specs.night_vision_range_m else "-",
            "field_of_view_deg": f"{camera_specs.field_of_view_deg}\u00b0" if camera_specs.field_of_view_deg else "-",
            "lens": f"{camera_specs.lens_mm} mm" if camera_specs.lens_mm else "-",
            "frame_rate": f"{camera_specs.frame_rate_fps} fps" if camera_specs.frame_rate_fps else "-",
            "weatherproof": camera_specs.weatherproof_rating or "-",
            "connectivity": camera_specs.get_connectivity_display() if camera_specs.connectivity else "-",
            "power_source": camera_specs.get_power_source_display() if camera_specs.power_source else "-",
            "storage_support": camera_specs.storage_support or "-",
            "audio_support": "Yes" if camera_specs.audio_support else "No",
            "ai_detection": "Yes" if camera_specs.ai_detection else "No",
            "warranty_years": f"{camera_specs.warranty_years} year(s)" if camera_specs.warranty_years else "-",
        }

    return {}


def _build_compare_specs(product):
    """Return machine-readable spec keys for compare and other API consumers."""
    spec_type = get_product_spec_type(product)

    if spec_type == SPEC_TYPE_CCTV:
        return _build_cctv_compare_specs(product)

    if spec_type == SPEC_TYPE_VIDEO_DOOR_PHONE:
        return {
            "screen_size": product.screen_size or "-",
            "camera_resolution": product.camera_resolution or "-",
            "night_vision": "Yes" if product.night_vision else "No",
            "connectivity_type": product.get_connectivity_type_display() if product.connectivity_type else "-",
            "unlock_method": product.get_unlock_method_display() if product.unlock_method else "-",
            "audio_communication": "Yes" if product.audio_communication else "No",
            "mobile_app_support": "Yes" if product.mobile_app_support else "No",
            "storage_support": product.storage_support_vdp or "-",
            "power_source": product.get_power_source_vdp_display() if product.power_source_vdp else "-",
            "installation_type": product.get_installation_type_display() if product.installation_type else "-",
            "warranty": product.warranty_vdp or "-",
        }

    if spec_type == SPEC_TYPE_BIOMETRIC:
        biometric_specs = product.biometric_specs if hasattr(product, "biometric_specs") else None
        if biometric_specs:
            return {
                "authentication_method": biometric_specs.authentication_method or "-",
                "user_capacity": str(biometric_specs.user_capacity) if biometric_specs.user_capacity else "-",
                "fingerprint_sensor": biometric_specs.fingerprint_sensor or "-",
                "face_recognition": "Yes" if biometric_specs.face_recognition else "No",
                "card_support": "Yes" if biometric_specs.card_support else "No",
                "connectivity": biometric_specs.connectivity or "-",
                "power_supply": biometric_specs.power_supply or "-",
            }

    if spec_type == SPEC_TYPE_SMART_LOCK:
        smartlock_specs = product.smartlock_specs if hasattr(product, "smartlock_specs") else None
        if smartlock_specs:
            return {
                "unlock_methods": smartlock_specs.unlock_methods or "-",
                "connectivity": smartlock_specs.connectivity or "-",
                "battery_life": smartlock_specs.battery_life or "-",
                "emergency_unlock": "Yes" if smartlock_specs.emergency_unlock else "No",
            }

    if spec_type == SPEC_TYPE_NETWORK:
        network_specs = product.network_specs if hasattr(product, "network_specs") else None
        if network_specs:
            return {
                "ports": str(network_specs.ports) if network_specs.ports else "-",
                "bandwidth": network_specs.bandwidth or "-",
                "poe_support": "Yes" if network_specs.poe_support else "No",
            }

    return {}


def _build_product_specs(product):
    """Return a list of spec dicts with label, value, and icon for detail pages."""
    spec_type = get_product_spec_type(product)
    compare_specs = _build_compare_specs(product)
    specs_list = []

    def add_spec(label, value_key, icon):
        val = compare_specs.get(value_key, "-")
        if val and val != "-":
            specs_list.append({"label": label, "value": val, "icon": icon})

    if spec_type == SPEC_TYPE_CCTV and compare_specs:
        add_spec("Camera Type", "camera_type", "bi-camera-video")
        add_spec("Resolution", "resolution_mp", "bi-display")
        add_spec("Lens", "lens", "bi-eye")
        add_spec("Field of View", "field_of_view_deg", "bi-arrows-expand")
        add_spec("Night Vision", "night_vision_range_m", "bi-moon-stars")
        add_spec("Frame Rate", "frame_rate", "bi-speedometer2")
        add_spec("Weatherproof", "weatherproof", "bi-cloud-rain")
        add_spec("Connectivity", "connectivity", "bi-wifi")
        add_spec("Power Source", "power_source", "bi-lightning-charge")
        add_spec("Storage Support", "storage_support", "bi-sd-card")
        add_spec("Two-Way Audio", "audio_support", "bi-mic")
        add_spec("AI Detection", "ai_detection", "bi-cpu")
        add_spec("Warranty", "warranty_years", "bi-shield-check")

    elif spec_type == SPEC_TYPE_VIDEO_DOOR_PHONE and compare_specs:
        add_spec("Screen Size", "screen_size", "bi-display")
        add_spec("Camera Resolution", "camera_resolution", "bi-camera")
        add_spec("Night Vision", "night_vision", "bi-moon-stars")
        add_spec("Connectivity", "connectivity_type", "bi-wifi")
        add_spec("Unlock Method", "unlock_method", "bi-unlock")
        add_spec("Two-Way Audio", "audio_communication", "bi-mic")
        add_spec("Mobile App", "mobile_app_support", "bi-phone")
        add_spec("Storage", "storage_support", "bi-sd-card")
        add_spec("Power Source", "power_source", "bi-lightning-charge")
        add_spec("Installation", "installation_type", "bi-tools")
        add_spec("Warranty", "warranty", "bi-shield-check")

    elif spec_type == SPEC_TYPE_BIOMETRIC and compare_specs:
        add_spec("Authentication Method", "authentication_method", "bi-fingerprint")
        add_spec("User Capacity", "user_capacity", "bi-people")
        add_spec("Fingerprint Sensor", "fingerprint_sensor", "bi-fingerprint")
        add_spec("Face Recognition", "face_recognition", "bi-person-bounding-box")
        add_spec("Card Support", "card_support", "bi-credit-card-2-front")
        add_spec("Connectivity", "connectivity", "bi-wifi")
        add_spec("Power Supply", "power_supply", "bi-power")

    elif spec_type == SPEC_TYPE_SMART_LOCK and compare_specs:
        add_spec("Unlock Methods", "unlock_methods", "bi-key")
        add_spec("Connectivity", "connectivity", "bi-wifi")
        add_spec("Battery Life", "battery_life", "bi-battery-half")
        add_spec("Emergency Unlock", "emergency_unlock", "bi-shield-exclamation")

    elif spec_type == SPEC_TYPE_NETWORK and compare_specs:
        add_spec("Ports", "ports", "bi-ethernet")
        add_spec("Bandwidth", "bandwidth", "bi-activity")
        add_spec("PoE Support", "poe_support", "bi-plug")

    # Add shared stock info if not already there
    if product.stock is not None:
        specs_list.append({"label": "Stock Available", "value": f"{product.stock} Units", "icon": "bi-boxes"})

    return specs_list


def _catalog_seo(request, category, query, page_obj, is_filtered):
    """Title, description, robots, canonical and breadcrumbs for the homepage, category and search listings."""
    page = page_obj.number
    page_suffix = f" (Page {page})" if page > 1 else ""
    is_empty = False
    if category:
        stats = Product.objects.filter(is_available=True, category=category).aggregate(n=Count("id"), low=Min("price"))
        title = f"{category.name} in Kozhikode, Kerala{page_suffix} | Eyetrack Solutions"
        if stats["n"]:
            description = (f"Buy {category.name} from Eyetrack Solutions: {stats['n']} product{'s' if stats['n'] != 1 else ''} "
                           f"from \u20b9{stats['low']:,.0f}, with professional installation and support across Kozhikode and Kerala.")
        else:
            is_empty = True
            description = (f"{category.name} from Eyetrack Solutions, with professional installation and support across "
                           f"Kozhikode and Kerala. Contact us for current models and prices.")
    elif query:
        title = f"Search results for \u201c{query}\u201d | Eyetrack Solutions"
        description = f"Products matching \u201c{query}\u201d at Eyetrack Solutions."
    else:
        title = f"CCTV Cameras & Installation in Kozhikode{page_suffix} | Eyetrack Solutions"
        description = ("CCTV cameras, smart locks, video door phones and biometric systems with professional "
                       "installation across Kozhikode and Kerala. Book a free site survey.")

    base = request.build_absolute_uri(request.path)
    canonical = base if page == 1 else f"{base}?page={page}"
    breadcrumbs = [("Home", request.build_absolute_uri("/"))]
    if category:
        breadcrumbs.append((category.name, base))
    return {
        "seo_title": title,
        "seo_description": description,
        # Search results, filtered or sorted views and empty categories are thin pages; keep them out of the index.
        "seo_robots": "noindex, follow" if is_filtered or is_empty else "index, follow, max-image-preview:large",
        "seo_canonical": canonical,
        "seo_breadcrumbs": breadcrumbs if category else [],
    }


def product_list(request, category_slug=None):
    category = None
    filter_categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    products_qs = Product.objects.filter(is_available=True).select_related("category")

    # Fetch wishlist item IDs for the current user
    wishlist_item_ids = []
    if request.user.is_authenticated:
        wishlist_item_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_qs = products_qs.filter(category=category)

    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "featured")
    in_stock = request.GET.get("in_stock")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    resolution = request.GET.get("resolution")
    has_ai = request.GET.get("has_ai")

    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if in_stock == "1":
        products_qs = products_qs.filter(stock__gt=0)
        
    if resolution and str(resolution).strip() != "":
        try:
            float(str(resolution).strip())
            products_qs = products_qs.filter(camera_specs__resolution_mp=str(resolution).strip())
        except ValueError:
            resolution = ""
            
    if has_ai == "1":
        products_qs = products_qs.filter(camera_specs__ai_detection=True)

    try:
        if min_price and str(min_price).strip() != "":
            products_qs = products_qs.filter(price__gte=float(str(min_price).strip()))
    except (ValueError, TypeError):
        min_price = ""
        
    try:
        if max_price and str(max_price).strip() != "":
            products_qs = products_qs.filter(price__lte=float(str(max_price).strip()))
    except (ValueError, TypeError):
        max_price = ""

    if sort == "price_asc":
        products_qs = products_qs.order_by("price")
    elif sort == "price_desc":
        products_qs = products_qs.order_by("-price")
    elif sort == "name_asc":
        products_qs = products_qs.order_by("name")
    elif sort == "newest":
        products_qs = products_qs.order_by("-created_at")
    else:
        sort = "featured"
        products_qs = products_qs.order_by("-stock", "-created_at")

    # Annotate per-product review stats for card-level star display
    products_qs = products_qs.annotate(
        avg_rating=Avg('reviews__rating', filter=Q(reviews__status=True)),
        review_count=Count('reviews', filter=Q(reviews__status=True), distinct=True),
    )

    # Get unique resolutions for filter dropdown
    resolutions = CameraSpecification.objects.exclude(resolution_mp__isnull=True).values_list('resolution_mp', flat=True).distinct()

    # Pagination — 12 products per page
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    featured_products = Product.objects.filter(is_available=True, stock__gt=0).order_by("-stock", "-created_at")[:4]
    top_sellers = Product.objects.filter(is_available=True).order_by("-created_at")[:6]
    price_range = Product.objects.filter(is_available=True).aggregate(min_price=Min("price"), max_price=Max("price"))

    total_product_count = Product.objects.filter(is_available=True).count()
    new_cutoff = timezone.now() - timedelta(days=30)
    popular_ids_qs = (
        OrderItem.objects.values('product_id')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:8]
    )
    popular_product_ids = frozenset(item['product_id'] for item in popular_ids_qs)

    # Build a query param string without ?page= so pagination links can append ?page=N
    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_string = query_params.urlencode()  # e.g. "q=camera&sort=price_asc"

    context = {
        "category": category,
        "filter_categories": filter_categories,
        "products": page_obj,       # template iterates this for the visible page
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": query_string, # for preserving filter params in pagination links
        "featured_products": featured_products,
        "top_sellers": top_sellers,
        "result_count": paginator.count,
        "q": query,
        "sort": sort,
        "in_stock": in_stock == "1",
        "min_price": min_price or "",
        "max_price": max_price or "",
        "resolution": resolution or "",
        "has_ai": has_ai == "1",
        "available_resolutions": resolutions,
        "min_catalog_price": price_range["min_price"] or 0,
        "max_catalog_price": price_range["max_price"] or 0,
        "wishlist_item_ids": wishlist_item_ids,
        "total_product_count": total_product_count,
        "new_cutoff": new_cutoff,
        "popular_product_ids": popular_product_ids,
    }

    context.update(_catalog_seo(request, category, query, page_obj,
                                is_filtered=bool(query or in_stock == "1" or min_price or max_price
                                                 or resolution or has_ai == "1" or sort != "featured")))

    # Homepage-only sections (testimonials, installation gallery, FAQ, quote form)
    is_landing = not category and not query and page_obj.number == 1
    context["is_landing"] = is_landing
    if is_landing:
        from orders.models import InstallationPhoto
        from support.forms import QuoteRequestForm
        from support.models import FAQ

        context["testimonials"] = (
            Review.objects.filter(status=True, rating__gte=4)
            .exclude(review="")
            .select_related("user", "product")
            .order_by("-created_at")[:6]
        )
        context["installation_photos"] = (
            InstallationPhoto.objects.filter(label=InstallationPhoto.PhotoLabel.AFTER)
            .select_related("booking")
            .order_by("-uploaded_at")[:8]
        )
        context["home_faqs"] = FAQ.objects.filter(is_active=True).order_by("order", "created_at")[:6]
        context["featured_projects"] = Project.objects.filter(is_published=True, is_featured=True).order_by("order", "-completed_on")[:4]
        context["quote_form"] = QuoteRequestForm()

    return render(request, "store/product_list.html", context)


def check_serviceability(request):
    """
    API endpoint to check if a pincode is serviceable.
    Returns delivery and installation availability.
    """
    pincode = request.GET.get('pincode', '').strip()
    product_id = request.GET.get('product_id')
    
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return JsonResponse({'ok': False, 'message': 'Please enter a valid 6-digit pincode.'}, status=400)
    
    # Store in session for persistence
    request.session['user_pincode'] = pincode
    
    area = ServiceableArea.objects.filter(pincode=pincode).first()
    
    if not area:
        return JsonResponse({
            'ok': False,
            'is_serviceable': False,
            'message': 'Service currently unavailable for this location.',
            'contact_support': True
        })
    
    if not area.delivery_available:
        return JsonResponse({
            'ok': False,
            'is_serviceable': False,
            'message': 'We do not deliver to this location yet.',
            'contact_support': True
        })
    
    return JsonResponse({
        'ok': True,
        'is_serviceable': True,
        'delivery_available': area.delivery_available,
        'installation_available': area.installation_available,
        'estimated_days': area.estimated_delivery_days,
        'delivery_charge': float(area.delivery_charge),
        'message': f'Great! We deliver to {pincode} in {area.estimated_delivery_days} days.'
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_available=True)
    related_products = (
        Product.objects.filter(category=product.category, is_available=True)
        .exclude(id=product.id)
        .order_by("-created_at")[:4]
    )
    if not related_products.exists():
        related_products = Product.objects.filter(is_available=True).exclude(id=product.id).order_by("-created_at")[:4]

    # Build spec chips for the quick hero badge strip
    specs = []
    spec_type = get_product_spec_type(product)
    compare_specs = _build_compare_specs(product)
    try:
        if spec_type == SPEC_TYPE_CCTV:
            if compare_specs.get("ai_detection") == "Yes":
                specs.append("AI Detection")
            if compare_specs.get("night_vision_range_m") not in (None, "", "-"):
                specs.append(f"Night Vision {compare_specs['night_vision_range_m']}")
            if compare_specs.get("weatherproof") not in (None, "", "-"):
                specs.append(compare_specs["weatherproof"])
            if compare_specs.get("connectivity") not in (None, "", "-"):
                specs.append(compare_specs["connectivity"])
            if compare_specs.get("resolution_mp") not in (None, "", "-"):
                specs.append(compare_specs["resolution_mp"])
        elif spec_type == SPEC_TYPE_VIDEO_DOOR_PHONE:
            if compare_specs.get("screen_size") not in (None, "", "-"):
                specs.append(compare_specs["screen_size"])
            if compare_specs.get("camera_resolution") not in (None, "", "-"):
                specs.append(compare_specs["camera_resolution"])
            if compare_specs.get("night_vision") == "Yes":
                specs.append("Night Vision")
            if compare_specs.get("mobile_app_support") == "Yes":
                specs.append("Mobile App")
        elif spec_type == SPEC_TYPE_BIOMETRIC:
            if compare_specs.get("authentication_method") not in (None, "", "-"):
                specs.append(compare_specs["authentication_method"])
            if compare_specs.get("face_recognition") == "Yes":
                specs.append("Face Recognition")
            if compare_specs.get("card_support") == "Yes":
                specs.append("Card Support")
        elif spec_type == SPEC_TYPE_SMART_LOCK:
            if compare_specs.get("unlock_methods") not in (None, "", "-"):
                specs.append(compare_specs["unlock_methods"])
            if compare_specs.get("connectivity") not in (None, "", "-"):
                specs.append(compare_specs["connectivity"])
        elif spec_type == SPEC_TYPE_NETWORK:
            if compare_specs.get("ports") not in (None, "", "-"):
                specs.append(f"{compare_specs['ports']} Ports")
            if compare_specs.get("poe_support") == "Yes":
                specs.append("PoE Supported")
    except Exception:
        pass

    if not specs:
        specs = ["Professional Build"]

    product_specs = _build_product_specs(product)
    
    # Split highlights into a list
    product_highlights = []
    if product.highlights:
        product_highlights = [h.strip() for h in product.highlights.split('\n') if h.strip()]

    # Review sorting
    review_sort = request.GET.get('review_sort', 'newest')
    reviews_qs = Review.objects.filter(product=product, status=True)
    if review_sort == 'highest':
        reviews_qs = reviews_qs.order_by('-rating', '-created_at')
    elif review_sort == 'lowest':
        reviews_qs = reviews_qs.order_by('rating', '-created_at')
    else:
        review_sort = 'newest'
        reviews_qs = reviews_qs.order_by('-created_at')

    # Annotate with helpful vote count
    reviews = reviews_qs.annotate(
        helpful_count=Count('helpful_votes', filter=Q(helpful_votes__is_helpful=True))
    )

    # Rating statistics
    avg_rating = product.averageReview()
    total_reviews_count = reviews.count()

    # Build star display list: 'full', 'half', or 'empty' for each of 5 stars
    rating_stars = []
    for i in range(1, 6):
        if avg_rating >= i:
            rating_stars.append('full')
        elif avg_rating >= i - 0.5:
            rating_stars.append('half')
        else:
            rating_stars.append('empty')

    # Per-star breakdown (5 → 1)
    rating_breakdown = []
    for star in range(5, 0, -1):
        cnt = Review.objects.filter(
            product=product, status=True,
            rating__gte=star - 0.5, rating__lt=star + 0.5
        ).count()
        pct = round(cnt / total_reviews_count * 100) if total_reviews_count > 0 else 0
        rating_breakdown.append({'star': star, 'count': cnt, 'percent': pct})

    # Warranty display — check specs hierarchy
    warranty_display = None
    try:
        if product.warranty:
            warranty_display = product.warranty
        else:
            try:
                cs = product.camera_specs
                if cs.warranty_years:
                    warranty_display = f"{cs.warranty_years} Year{'s' if cs.warranty_years != 1 else ''}"
            except Exception:
                pass
            if not warranty_display and product.warranty_vdp:
                warranty_display = product.warranty_vdp
    except Exception:
        pass

    # Wishlist status
    wishlist_item_ids = []
    if request.user.is_authenticated:
        wishlist_item_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    # Check if user can review (must have a delivered order containing this product)
    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__order_status=Order.OrderStatus.DELIVERED
        ).exists()

    summary = " ".join(strip_tags(product.description or "").split())
    seo_description = f"{product.name}: \u20b9{product.price:,.0f} at Eyetrack Solutions, Kozhikode."
    if summary:
        seo_description += " " + Truncator(summary).chars(149 - len(seo_description), truncate="\u2026")

    context = {
        "product": product,
        "seo_description": seo_description,
        "related_products": related_products,
        "specs": specs,
        "product_specs": product_specs,
        "product_highlights": product_highlights,
        "reviews": reviews,
        "review_sort": review_sort,
        "avg_rating": avg_rating,
        "total_reviews_count": total_reviews_count,
        "rating_stars": rating_stars,
        "rating_breakdown": rating_breakdown,
        "warranty_display": warranty_display,
        "can_review": can_review,
        "wishlist_item_ids": wishlist_item_ids,
        "user_pincode": request.session.get('user_pincode', ''),
    }
    return render(request, "store/product_detail.html", context)


@login_required(login_url="login")
@require_POST
def submit_review(request, product_id):
    url = request.META.get("HTTP_REFERER")
    try:
        reviews = Review.objects.get(user__id=request.user.id, product__id=product_id)
        form = ReviewForm(request.POST, instance=reviews)
        form.save()
        
        # Handle new media uploads for existing review
        files = request.FILES.getlist('review_media')
        for f in files:
            is_video = f.content_type.startswith('video/')
            ReviewMedia.objects.create(review=reviews, file=f, is_video=is_video)
            
        messages.success(request, "Thank you! Your review has been updated.")
        return redirect(url)
    except Review.DoesNotExist:
        form = ReviewForm(request.POST)
        if form.is_valid():
            data = Review()
            data.subject = form.cleaned_data["subject"]
            data.rating = form.cleaned_data["rating"]
            data.review = form.cleaned_data["review"]
            data.ip = request.META.get("REMOTE_ADDR")
            data.product_id = product_id
            data.user_id = request.user.id
            data.save()
            
            # Handle media uploads
            files = request.FILES.getlist('review_media')
            for f in files:
                is_video = f.content_type.startswith('video/')
                ReviewMedia.objects.create(review=data, file=f, is_video=is_video)
                
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect(url)
        else:
            messages.error(request, "There was an error in your review submission.")
            return redirect(url)


def quick_view_product(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), id=product_id, is_available=True)
    data = {
        "ok": True,
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "url": reverse("product_detail", kwargs={"slug": product.slug}),
            "add_to_cart_url": reverse("add_to_cart", kwargs={"product_id": product.id}),
            "price": str(product.price),
            "stock": product.stock,
            "category": product.category.name,
            "category_id": product.category.id,
            "category_slug": product.category.slug,
            "description": product.description,
            "image": product.image.url if product.image else "",
            "specs": _build_compare_specs(product),
            "display_specs": _build_product_specs(product),
        },
    }
    return JsonResponse(data)


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    next_url = request.POST.get("next") or "cart"
    wants_json = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )
    if product.stock <= 0:
        msg = "This product is currently out of stock."
        if wants_json:
            return JsonResponse({"ok": False, "message": msg}, status=400)
        messages.error(request, msg)
        return redirect(next_url)

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    current_qty = cart.get(product_id_str, 0)

    # Get quantity from POST, default to 1
    try:
        requested_qty = int(request.POST.get("quantity", 1))
        if requested_qty < 1:
            requested_qty = 1
    except (ValueError, TypeError):
        requested_qty = 1

    if current_qty + requested_qty > product.stock:
        msg = f"Only {product.stock} unit(s) available for this item. You already have {current_qty} in cart."
        if wants_json:
            return JsonResponse({"ok": False, "message": msg}, status=400)
        messages.warning(request, msg)
        return redirect(next_url)

    cart[product_id_str] = current_qty + requested_qty
    request.session["cart"] = cart
    
    cart_installations = request.session.get("cart_installations", {})
    if "is_detail_form" in request.POST:
        wants_installation = request.POST.get("wants_installation") in ["true", "on", "1"]
        if wants_installation and product.installation_available:
            cart_installations[product_id_str] = True
        else:
            cart_installations.pop(product_id_str, None)
        request.session["cart_installations"] = cart_installations
        request.session.modified = True

    msg = "Item added to cart."
    if wants_json:
        return JsonResponse(
            {
                "ok": True,
                "message": msg,
                "cart_count": _cart_total_items(cart),
                "item": {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "quantity": cart[product_id_str],
                    "slug": product.slug,
                    "image": product.image.url if product.image else "",
                    "installation_available": product.installation_available,
                    "installation_charge": str(product.installation_charge),
                },
                "cart_url": reverse("cart"),
            }
        )
    messages.success(request, msg)
    return redirect(next_url)


@require_POST
def update_cart_installation(request, product_id):
    """AJAX: Add or remove installation service for a cart item."""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    action = request.POST.get("action", "add")  # 'add' or 'remove'

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str not in cart:
        return JsonResponse({"ok": False, "message": "Item not in cart."}, status=400)

    cart_installations = request.session.get("cart_installations", {})

    if action == "add" and product.installation_available:
        cart_installations[product_id_str] = True
        has_installation = True
    else:
        cart_installations.pop(product_id_str, None)
        has_installation = False

    request.session["cart_installations"] = cart_installations
    request.session.modified = True

    qty = cart.get(product_id_str, 1)
    total_charge = float(product.installation_charge) * qty if has_installation else 0

    return JsonResponse(
        {
            "ok": True,
            "has_installation": has_installation,
            "installation_charge": str(product.installation_charge),
            "total_charge": str(total_charge),
            "message": (
                f"Installation (\u20b9{product.installation_charge}/unit) added!"
                if has_installation
                else "Installation removed."
            ),
        }
    )


def cart_view(request):
    cart = request.session.get("cart", {})
    cart_installations = request.session.get("cart_installations", {})
    products = []
    total = Decimal("0.00")
    total_installation_charge = Decimal("0.00")
    cleaned_cart = {}  # Track which items are still valid
    cleaned_installations = {}

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, is_available=True).first()
        if not product:
            # Skip unavailable/deleted products but don't add to cleaned_cart
            continue
        # Product is valid, add to cleaned cart
        has_install = str(product_id) in cart_installations and product.installation_available
        if has_install:
            cleaned_installations[str(product_id)] = True
            
        install_cost = (product.installation_charge * quantity) if has_install else Decimal("0.00")
        
        cleaned_cart[product_id] = quantity
        product.quantity = quantity
        product.subtotal = product.price * quantity
        product.install_cost = install_cost
        product.has_install = has_install
        
        total += product.subtotal
        total_installation_charge += install_cost
        products.append(product)

    # Update session with cleaned cart (remove invalid items)
    if cleaned_cart != cart or cleaned_installations != cart_installations:
        request.session["cart"] = cleaned_cart
        request.session["cart_installations"] = cleaned_installations
        request.session.modified = True

    # Determine if any product in the cart requires shipping
    requires_shipping = any(not p.is_free_shipping for p in products)
    
    shipping = Decimal("0.00")
    if requires_shipping:
        # Default logic: fallback to 0 (FREE) or 0 if over 5000
        shipping = Decimal("0.00") if total >= Decimal("5000.00") else Decimal("0.00")
        
        # Check if we have a pincode in session to refine the charge
        pincode = request.session.get('user_pincode')
        if pincode:
            from store.models import ServiceableArea
            area = ServiceableArea.objects.filter(pincode=pincode).first()
            if area:
                shipping = Decimal("0.00") if total >= Decimal("5000.00") else area.delivery_charge
    
    # Calculate Coupon Discount
    coupon_id = request.session.get("coupon_id")
    discount_amount = Decimal("0.00")
    active_coupon = None
    
    if coupon_id:
        active_coupon = Coupon.objects.filter(id=coupon_id).first()
        if active_coupon:
            valid, msg = active_coupon.is_valid()
            if valid:
                discount_amount = (total * Decimal(str(active_coupon.discount_percentage))) / Decimal("100")
                if active_coupon.max_discount_amount and discount_amount > active_coupon.max_discount_amount:
                    discount_amount = active_coupon.max_discount_amount
            else:
                # Remove invalid coupon from session
                del request.session["coupon_id"]
                active_coupon = None

    tax = Decimal("0.00")
    grand_total = (total - discount_amount) + shipping + tax + total_installation_charge
    
    # Smart Recommendations based on cart contents
    cart_category_ids = list(set([p.category.id for p in products if p.category]))
    recommended_products = Product.objects.filter(is_available=True, stock__gt=0).exclude(
        id__in=[item.id for item in products]
    )
    if cart_category_ids:
        recommended_products = recommended_products.order_by(
            Case(
                When(category_id__in=cart_category_ids, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            '-stock'
        )
    else:
        recommended_products = recommended_products.order_by('-stock')
        
    recommended_products = recommended_products[:4]

    context = {
        "products": products,
        "total": total,
        "total_installation_charge": total_installation_charge,
        "discount_amount": discount_amount,
        "active_coupon": active_coupon,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
        "recommended_products": recommended_products,
    }
    return render(request, "store/cart.html", context)


@require_POST
def remove_from_cart(request, product_id):
    next_url = request.POST.get("next") or "cart"
    cart = request.session.get("cart", {})
    cart_installations = request.session.get("cart_installations", {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    if str(product_id) in cart_installations:
        del cart_installations[str(product_id)]
    request.session["cart"] = cart
    request.session["cart_installations"] = cart_installations
    messages.info(request, "Item removed from cart.")
    return redirect(next_url)


@require_POST
def update_cart(request, product_id, action):
    next_url = request.POST.get("next") or "cart"
    cart = request.session.get("cart", {})
    product_id = str(product_id)
    if product_id in cart:
        if action == "increase":
            product = Product.objects.filter(id=product_id, is_available=True).first()
            if not product:
                messages.error(request, "This product is no longer available.")
                del cart[product_id]
            elif cart[product_id] >= product.stock:
                messages.warning(request, f"Only {product.stock} unit(s) available for this item.")
            else:
                cart[product_id] += 1
        elif action == "decrease":
            cart[product_id] -= 1
            if cart[product_id] <= 0:
                del cart[product_id]
                cart_inst = request.session.get("cart_installations", {})
                if product_id in cart_inst:
                    del cart_inst[product_id]
                    request.session["cart_installations"] = cart_inst
    request.session["cart"] = cart
    return redirect(next_url)


def checkout(request):
    cart = request.session.get("cart", {})
    cart_installations = request.session.get("cart_installations", {})
    if not cart:
        return redirect("product_list")

    product_quantities = {int(pid): qty for pid, qty in cart.items() if qty > 0}
    if not product_quantities:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    products = []
    subtotal_total = Decimal("0.00")
    total_installation_charge = Decimal("0.00")
    unavailable_items = []
    has_installation = False
    
    for product_id, quantity in product_quantities.items():
        try:
            product = Product.objects.select_related("category").get(id=product_id, is_available=True)
            subtotal = product.price * quantity
            subtotal_total += subtotal
            
            has_install = str(product_id) in cart_installations and product.installation_available
            install_cost = (product.installation_charge * quantity) if has_install else Decimal("0.00")
            total_installation_charge += install_cost
            if has_install:
                has_installation = True
                
            products.append({"product": product, "quantity": quantity, "subtotal": subtotal, "has_install": has_install, "install_cost": install_cost})
        except Product.DoesNotExist:
            unavailable_items.append(product_id)
    
    # If some items are unavailable, remove them from cart and notify user
    if unavailable_items:
        for item_id in unavailable_items:
            if str(item_id) in request.session.get('cart', {}):
                del request.session['cart'][str(item_id)]
        request.session.modified = True
        
        if not products:
            messages.error(request, "All items in your cart are no longer available. Your cart has been cleared.")
            return redirect("product_list")
        else:
            messages.warning(request, f"{len(unavailable_items)} item(s) in your cart are no longer available and have been removed.")

    # Calculate Discount
    coupon_id = request.session.get("coupon_id")
    discount_amount = Decimal("0.00")
    active_coupon = None
    if coupon_id:
        active_coupon = Coupon.objects.filter(id=coupon_id).first()
        if active_coupon:
            valid, _ = active_coupon.is_valid()
            if valid:
                discount_amount = (subtotal_total * Decimal(str(active_coupon.discount_percentage))) / Decimal("100")
                if active_coupon.max_discount_amount and discount_amount > active_coupon.max_discount_amount:
                    discount_amount = active_coupon.max_discount_amount

    if request.user.is_authenticated:
        saved_address_qs = request.user.addresses.all()
        default_address = saved_address_qs.filter(is_default=True).first() or saved_address_qs.first()
        selected_address_id = request.POST.get("saved_address", "").strip()
        selected_address = saved_address_qs.filter(pk=selected_address_id).first() if selected_address_id else None
        chosen_saved_address = selected_address if request.method == "POST" else None
        if selected_address is None:
            selected_address = default_address
            if request.method != "POST" and selected_address:
                selected_address_id = str(selected_address.id)
    else:
        saved_address_qs = []
        selected_address = None
        selected_address_id = None
        chosen_saved_address = None

    # Determine if any product in the cart requires shipping
    requires_shipping = any(not item['product'].is_free_shipping for item in products)
    
    shipping = Decimal("0.00")
    if requires_shipping:
        # Base shipping logic: default to 0 (FREE) or 0 if over 5000
        shipping = Decimal("0.00") if subtotal_total >= Decimal("5000.00") else Decimal("0.00")
        
        # If we have a selected address with a pincode, use that pincode's specific charge
        if selected_address and hasattr(selected_address, 'pincode'):
            from store.models import ServiceableArea
            area = ServiceableArea.objects.filter(pincode=selected_address.pincode).first()
            if area:
                shipping = Decimal("0.00") if subtotal_total >= Decimal("5000.00") else area.delivery_charge
        
        # If it's a POST request with a manual pincode entry
        manual_pincode = request.POST.get("addr_pincode", "").strip()
        if manual_pincode:
            from store.models import ServiceableArea
            area = ServiceableArea.objects.filter(pincode=manual_pincode).first()
            if area:
                shipping = Decimal("0.00") if subtotal_total >= Decimal("5000.00") else area.delivery_charge

    tax = Decimal("0.00")
    grand_total = (subtotal_total - discount_amount) + shipping + tax + total_installation_charge

    if request.method == "POST":
        checkout_initial = {
            "full_name": request.POST.get("full_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "address": request.POST.get("address", "").strip(),
        }
    else:
        checkout_initial = _build_checkout_form_initial(request.user, selected_address) if request.user.is_authenticated else {
            "full_name": "",
            "email": "",
            "phone": "",
            "address": "",
        }

    if request.method == "POST":
        full_name = checkout_initial["full_name"]
        email = checkout_initial["email"]
        phone = checkout_initial["phone"]
        address = checkout_initial["address"]

        if selected_address:
            selected_initial = _build_checkout_form_initial(request.user, selected_address)
            full_name = full_name or selected_initial["full_name"]
            email = email or selected_initial["email"]
            phone = phone or selected_initial["phone"]
            address = address or selected_initial["address"]
            checkout_initial.update(
                {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "address": address,
                }
            )

        if not all([full_name, email, phone]):
            messages.error(request, "Please fill in all required contact fields.")
        else:
            # Construct structured address
            addr_house = request.POST.get("addr_house", "").strip()
            addr_street = request.POST.get("addr_street", "").strip()
            addr_landmark = request.POST.get("addr_landmark", "").strip()
            addr_city = request.POST.get("addr_city", "").strip()
            addr_state = request.POST.get("addr_state", "").strip()
            addr_pincode = request.POST.get("addr_pincode", "").strip()

            # A chosen saved address satisfies the delivery address when the manual fields are left empty.
            use_saved_address = chosen_saved_address is not None and not any(
                [addr_house, addr_street, addr_landmark, addr_city, addr_state, addr_pincode]
            )
            if use_saved_address:
                addr_pincode = chosen_saved_address.pincode.strip()
            elif not all([addr_house, addr_street, addr_city, addr_state, addr_pincode]):
                messages.error(request, "Please fill in all required address fields including pincode.")
                return redirect("checkout")

            # Validate Serviceability
            from store.models import ServiceableArea
            area = ServiceableArea.objects.filter(pincode=addr_pincode).first()
            if not area or not area.delivery_available:
                messages.error(request, f"Sorry, delivery is currently not available to pincode {addr_pincode}.")
                return redirect("checkout")
            if has_installation and not area.installation_available:
                messages.error(request, f"Sorry, professional installation is not supported in pincode {addr_pincode}. Please remove installation from your cart or change the delivery address.")
                return redirect("checkout")

            if use_saved_address:
                address = _format_saved_address(chosen_saved_address)
            else:
                address_parts = [addr_house, addr_street]
                if addr_landmark:
                    address_parts.append(f"Landmark: {addr_landmark}")
                address_parts.append(f"{addr_city}, {addr_state} - {addr_pincode}")
                address = "\n".join(address_parts)
            installation_date = request.POST.get("installation_date")
            installation_time = request.POST.get("installation_time")
            
            if has_installation and (not installation_date or not installation_time):
                messages.error(request, "Please select your preferred installation date and time slot.")
                return redirect("checkout")

            with transaction.atomic():
                locked_products = (
                    Product.objects.select_for_update()
                    .filter(id__in=product_quantities.keys(), is_available=True)
                )
                locked_map = {p.id: p for p in locked_products}

                if len(locked_map) != len(product_quantities):
                    messages.error(request, "Some items in your cart are unavailable. Please review your cart.")
                    return redirect("cart")

                recalculated_subtotal = Decimal("0.00")
                recalculated_installation = Decimal("0.00")
                for product_id, quantity in product_quantities.items():
                    locked_product = locked_map[product_id]
                    if locked_product.stock < quantity:
                        messages.error(
                            request,
                            f"Insufficient stock for {locked_product.name}. "
                            f"Available: {locked_product.stock}, requested: {quantity}.",
                        )
                        return redirect("cart")
                    recalculated_subtotal += locked_product.price * quantity
                    if str(product_id) in cart_installations and locked_product.installation_available:
                        recalculated_installation += locked_product.installation_charge * quantity

                # Re-calculate shipping for the locked state
                requires_shipping_locked = any(not locked_map[pid].is_free_shipping for pid in product_quantities.keys())
                
                locked_shipping = Decimal("0.00")
                if requires_shipping_locked:
                    locked_shipping = Decimal("0.00") if recalculated_subtotal >= Decimal("5000.00") else Decimal("299.00")
                    # Use the actual area charge validated above
                    if area:
                         locked_shipping = Decimal("0.00") if recalculated_subtotal >= Decimal("5000.00") else area.delivery_charge
                
                locked_tax = Decimal("0.00")
                locked_grand_total = (recalculated_subtotal - discount_amount) + locked_shipping + locked_tax + recalculated_installation

                payment_method = request.POST.get("payment_method", Order.PaymentMethod.ONLINE)
                if payment_method not in dict(Order.PaymentMethod.choices):
                    payment_method = Order.PaymentMethod.ONLINE
                
                # Security: COD is now open to all users as per latest requirements.
                # Previously, this was restricted to verified mobile numbers.
                pass

                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    total=locked_grand_total,
                    coupon=active_coupon,
                    discount_amount=discount_amount,
                    total_installation_charge=recalculated_installation,
                    order_status=Order.OrderStatus.PENDING,
                    payment_method=payment_method,
                )
                
                # Trigger Notification for authenticated users - ONLY for COD. 
                # Online orders will get their notification AFTER payment verification.
                if request.user.is_authenticated and payment_method == Order.PaymentMethod.COD:
                    from accounts.models import Notification
                    Notification.send(
                        user=request.user,
                        title="Order Placed Successfully",
                        message=f"Your order {order.formatted_id} has been received and is currently being processed.",
                        notification_type=Notification.NotificationType.ORDER,
                        link=f"/accounts/orders/{order.id}/track/"
                    )
                
                # Increment coupon usage if applied
                if active_coupon:
                    active_coupon.current_uses += 1
                    active_coupon.save(update_fields=["current_uses"])
                    # Remove from session after order creation
                    del request.session["coupon_id"]

                if has_installation:
                    from orders.models import InstallationBooking
                    InstallationBooking.objects.create(
                        order=order,
                        preferred_date=installation_date,
                        preferred_time_slot=installation_time,
                    )

                if order.payment_method == Order.PaymentMethod.COD:
                    order.payment_status = Order.PaymentStatus.PENDING
                    order.save(update_fields=["payment_status"])

                for product_id, quantity in product_quantities.items():
                    product_instance = locked_map[product_id]
                    has_install = str(product_id) in cart_installations and product_instance.installation_available
                    OrderItem.objects.create(
                        order=order,
                        product=product_instance,
                        quantity=quantity,
                        price=product_instance.price,
                        has_installation=has_install,
                        installation_charge=product_instance.installation_charge if has_install else Decimal("0.00")
                    )

                # Deduct stock for ALL payment methods (COD and online).
                # Previously, COD orders never reduced stock because the
                # deduction only lived inside simulated_payment(). This block
                # runs atomically here, inside the same transaction.atomic().
                for product_id, quantity in product_quantities.items():
                    product_to_update = locked_map[product_id]
                    product_to_update.stock -= quantity
                    product_to_update.save(update_fields=["stock"])

                if order.payment_method == Order.PaymentMethod.COD:
                    Payment.objects.create(
                        order=order,
                        amount=locked_grand_total,
                        status="Pending",
                        payment_method="Cash on Delivery",
                    )
                    Shipment.objects.create(order=order)
                    base_url = request.build_absolute_uri("/")
                    transaction.on_commit(lambda: send_order_placed_email(order.pk, base_url=base_url))
                    request.session["cart"] = {}
                    request.session["latest_order_id"] = order.id
                    return redirect("order_success")

                Payment.objects.create(
                    order=order,
                    amount=locked_grand_total,
                    status="Pending",
                    payment_method="Razorpay",
                )
                Shipment.objects.create(order=order)
                # We SKIP send_order_placed_email here for online payments.
                # It will be sent in razorpay_callback after verification.
            # For guest (unauthenticated) orders, write a session token so only
            # the browser that placed this order can reach the payment page.
            if not request.user.is_authenticated:
                request.session["pending_guest_order_id"] = order.id
            return redirect("razorpay_checkout", order_id=order.id)

    context = {
        "products": products,
        "has_installation": has_installation,
        "total": subtotal_total,
        "total_installation_charge": total_installation_charge,
        "discount_amount": discount_amount,
        "active_coupon": active_coupon,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
        "saved_addresses": [_build_saved_address_option(request.user, address) for address in saved_address_qs],
        "selected_address_id": selected_address_id,
        "selected_address_display": _format_saved_address(selected_address) if selected_address_id and selected_address else "",
        "checkout_initial": checkout_initial,
        "min_install_date": (timezone.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
    }
    return render(request, "store/checkout.html", context)



def order_success(request):
    latest_order = None
    if request.user.is_authenticated:
        latest_order = request.user.orders.order_by("-created_at").first()
    
    if not latest_order:
        order_id = request.session.get("latest_order_id")
        if order_id:
            latest_order = Order.objects.filter(id=order_id).first()
            
    return render(request, "store/order_success.html", {"latest_order": latest_order})


@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip()
    if not code:
        return JsonResponse({"ok": False, "message": "Please enter a coupon code."})

    coupon = Coupon.objects.filter(code__iexact=code).first()
    if not coupon:
        return JsonResponse({"ok": False, "message": "Invalid coupon code."})

    is_valid, msg = coupon.is_valid()
    if not is_valid:
        return JsonResponse({"ok": False, "message": msg})

    # Store in session
    request.session["coupon_id"] = coupon.id
    return JsonResponse({"ok": True, "message": f"Coupon '{coupon.code}' applied successfully!"})


@require_POST
def remove_coupon(request):
    if "coupon_id" in request.session:
        del request.session["coupon_id"]
    return JsonResponse({"ok": True, "message": "Coupon removed."})



def razorpay_checkout(request, order_id):
    try:
        if request.user.is_authenticated:
            order = get_object_or_404(Order, id=order_id, user=request.user)
        else:
            # Guest orders: only the browser that placed the order holds the
            # session token.  Reject anything that doesn't match to prevent IDOR
            # enumeration attacks (CVE-class: Insecure Direct Object Reference).
            pending_id = request.session.get("pending_guest_order_id")
            if pending_id != order_id:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    "Access denied. This payment link is not valid for your session."
                )
            order = get_object_or_404(Order, id=order_id, user=None)
        
        if order.payment_method == Order.PaymentMethod.COD:
            messages.info(request, "This order is Cash On Delivery. No online payment is required.")
            return redirect("order_success")
            
        if order.order_status != Order.OrderStatus.PENDING:
            return redirect("order_history")

        # Validate Razorpay configuration
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not key_id or not key_secret or key_id == 'rzp_test_placeholder':
            messages.error(request, "Payment gateway is not properly configured. Please contact support.")
            return redirect("checkout")

        amount_in_paise = int(order.total * 100)
        
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            razorpay_order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"receipt_order_{order.id}",
                "payment_capture": 1 # Auto-capture payment
            }
            
            razorpay_order = client.order.create(data=razorpay_order_data)
            razorpay_order_id = razorpay_order['id']
        except Exception as e:
            messages.error(request, f"Razorpay API Error: {str(e)}")
            return redirect("checkout")
            
        # Save/Update payment record
        payment = order.payments.filter(status=Order.PaymentStatus.PENDING).first()
        if payment:
            payment.transaction_id = razorpay_order_id
            payment.save(update_fields=["transaction_id"])
            
        context = {
            "order": order,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_key_id": key_id,
            "amount": amount_in_paise,
            "currency": "INR",
            "callback_url": request.build_absolute_uri(reverse("razorpay_callback")),
        }
        return render(request, "store/payment.html", context)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Critical error in razorpay_checkout: {str(e)}", exc_info=True)
        messages.error(request, "A system error occurred while processing your payment request. Please try again later.")
        return redirect("checkout")


@require_POST
def razorpay_callback(request):
    """
    Callback view for Razorpay to verify payment signature.
    """
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    import logging
    logger = logging.getLogger(__name__)

    try:
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            logger.error(f"Missing Razorpay callback data: payment_id={razorpay_payment_id}, order_id={razorpay_order_id}")
            messages.error(request, "Payment failed: Missing transaction data.")
            return redirect("checkout")

        client = razorpay.Client(auth=(key_id, key_secret))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        # Verify the signature
        client.utility.verify_payment_signature(params_dict)
        
        # On success, update the order and payment
        payment = get_object_or_404(Payment, transaction_id=razorpay_order_id)
        order = payment.order
        
        base_url = request.build_absolute_uri("/")
        with transaction.atomic():
            payment.status = "Paid"
            payment.paid_at = timezone.now()
            payment.transaction_id = razorpay_payment_id # Update with actual payment ID
            payment.save(update_fields=["status", "paid_at", "transaction_id"])
            
            order.order_status = Order.OrderStatus.CONFIRMED
            order.payment_status = "Paid"
            order.save(update_fields=["order_status", "payment_status"])
            
            # Send placement confirmation email now that payment is confirmed
            transaction.on_commit(lambda: send_order_placed_email(order.pk, base_url=base_url))
            
            # Send invoice email
            transaction.on_commit(lambda: send_order_invoice_email(order.pk, base_url=base_url))
            
            # Send Admin Notification
            transaction.on_commit(
                lambda: send_email_async(send_admin_order_notification_email, order.id, event_type="placed", base_url=base_url)
            )
            
            # Send final confirmation notification to customer
            if order.user:
                from accounts.models import Notification
                Notification.send(
                    user=order.user,
                    title="Order Confirmed & Paid",
                    message=f"Payment for order {order.formatted_id} was successful. We have started processing your order!",
                    notification_type=Notification.NotificationType.ORDER,
                    link=f"/accounts/orders/{order.id}/track/"
                )
            
        messages.success(request, f"Payment successful! Order {order.formatted_id} confirmed.")
        request.session["cart"] = {}
        request.session["latest_order_id"] = order.id
        return redirect("order_success")
        
    except Exception as e:
        logger.error(f"Razorpay verification failed: {str(e)}", exc_info=True)
        # If verification fails
        payment = Payment.objects.filter(transaction_id=razorpay_order_id).first()
        if payment:
            payment.status = "Failed"
            payment.save(update_fields=["status"])
        
        messages.error(request, f"Payment verification failed: {str(e)}. Please contact support.")
        return redirect("order_history")


@csrf_exempt
def razorpay_webhook(request):
    """
    Razorpay Webhook handler for production reliability.
    """
    import logging
    logger = logging.getLogger(__name__)

    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body.decode('utf-8')
    signature = request.headers.get('X-Razorpay-Signature')
    secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)

    if not secret:
        logger.warning("Razorpay webhook received but RAZORPAY_WEBHOOK_SECRET is not configured.")
        return HttpResponse("Webhook secret not configured", status=400)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_webhook_signature(payload, signature, secret)
    except Exception as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return HttpResponse("Invalid signature", status=400)

    import json
    try:
        data = json.loads(payload)
        event = data.get('event')

        # Handle payment.captured or order.paid events
        if event in ['payment.captured', 'order.paid']:
            payment_data = data.get('payload', {}).get('payment', {}).get('entity', {})
            razorpay_order_id = payment_data.get('order_id')
            razorpay_payment_id = payment_data.get('id')

            payment = Payment.objects.filter(transaction_id=razorpay_order_id, status="Pending").first()
            if payment:
                order = payment.order
                base_url = request.build_absolute_uri("/")
                
                with transaction.atomic():
                    if payment.status != "Paid":
                        payment.status = "Paid"
                        payment.paid_at = timezone.now()
                        payment.transaction_id = razorpay_payment_id
                        payment.save(update_fields=["status", "paid_at", "transaction_id"])
                        
                        if order.payment_status != "Paid":
                            order.order_status = Order.OrderStatus.CONFIRMED
                            order.payment_status = "Paid"
                            order.save(update_fields=["order_status", "payment_status"])
                            
                            # Trigger emails and notifications
                            transaction.on_commit(lambda: send_order_placed_email(order.pk, base_url=base_url))
                            transaction.on_commit(lambda: send_order_invoice_email(order.pk, base_url=base_url))
                            if order.user:
                                from accounts.models import Notification
                                Notification.send(
                                    user=order.user,
                                    title="Order Confirmed (Webhook)",
                                    message=f"Payment for order {order.formatted_id} was verified via webhook.",
                                    notification_type=Notification.NotificationType.ORDER,
                                    link=f"/accounts/orders/{order.id}/track/"
                                )
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return HttpResponse(status=500)


@require_POST
def cancel_order(request, order_id):
    """
    Allows a user to cancel a pending order.
    """
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        pending_id = request.session.get("pending_guest_order_id")
        if pending_id != order_id:
            return HttpResponseForbidden("Access denied.")
        order = get_object_or_404(Order, id=order_id, user=None)
    
    if order.order_status == Order.OrderStatus.PENDING:
        order.order_status = Order.OrderStatus.CANCELLED
        order.save(update_fields=["order_status"])
        messages.success(request, f"Order {order.formatted_id} has been cancelled and items have been returned to stock.")
    else:
        messages.error(request, "This order cannot be cancelled at this stage.")
        
    return redirect("order_history")


@require_POST
def notify_stock(request, product_id):
    """AJAX: Register an email to be notified when an out-of-stock product is available again."""
    product = get_object_or_404(Product, id=product_id, is_available=True)

    if product.stock > 0:
        return JsonResponse({'ok': False, 'message': 'This product is already in stock!'})

    email = request.POST.get('email', '').strip().lower()
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return JsonResponse({'ok': False, 'message': 'Please enter a valid email address.'})

    _, created = StockNotification.objects.get_or_create(product=product, email=email)
    if created:
        return JsonResponse({'ok': True, 'message': "Got it! We'll email you the moment it's back in stock."})
    return JsonResponse({'ok': True, 'message': "You're already on the notification list for this product."})


@require_POST
def vote_review_helpful(request, review_id):
    """AJAX: Toggle a helpful/not-helpful vote on a review, keyed by session."""
    review = get_object_or_404(Review, id=review_id, status=True)
    is_helpful_val = request.POST.get('is_helpful', 'true').lower() == 'true'

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    existing = ReviewHelpful.objects.filter(review=review, session_key=session_key).first()
    if existing:
        if existing.is_helpful == is_helpful_val:
            existing.delete()
            action = 'removed'
        else:
            existing.is_helpful = is_helpful_val
            existing.save(update_fields=['is_helpful'])
            action = 'updated'
    else:
        ReviewHelpful.objects.create(review=review, session_key=session_key, is_helpful=is_helpful_val)
        action = 'added'

    helpful_count = ReviewHelpful.objects.filter(review=review, is_helpful=True).count()
    return JsonResponse({'ok': True, 'action': action, 'helpful_count': helpful_count})


def solutions_page(request):
    return render(request, "store/solutions.html")


def about_page(request):
    return render(request, "store/about.html")


def services_page(request):
    from django.contrib.auth.models import User
    context = {
        'is_authenticated': request.user.is_authenticated,
        'login_url': '/accounts/login/?next=/services/',
    }
    return render(request, "store/services.html", context)


def support_page(request):
    return render(request, "store/support.html")


# Single source for the FAQ page: the visible questions and the FAQPage
# structured data (JSON-LD) are both built from this list, so they always match.
FAQ_SECTIONS = (
    {
        "id": "buying",
        "title": "Buying & Checkout",
        "icon": "bi-bag-check",
        "items": (
            ("Is payment secure on this website?",
             "Yes, we use industry-standard encryption and secure payment gateways (like Razorpay) to ensure your transaction data is fully protected."),
            ("What payment methods do you accept?",
             "We accept all major Credit/Debit cards, Net Banking, UPI, and popular mobile wallets. Cash on Delivery (COD) is also available for select locations in Kerala."),
            ("Can I track my order after purchase?",
             "Yes, once your order is confirmed, you can track its status in real-time from your account dashboard under 'Order History' or via the tracking link sent to your email."),
            ("Do you ship pan-India?",
             "We currently specialize in Kerala with a focus on Kozhikode. You can check your pincode on any product page for instant serviceability and delivery estimates."),
        ),
    },
    {
        "id": "installation",
        "title": "Installation",
        "icon": "bi-tools",
        "items": (
            ("Do you provide professional installation?",
             "Yes, we provide expert on-site installation for all our products. You can opt for installation during checkout for serviceable locations in and around Kozhikode."),
            ("How long does installation take?",
             "Most residential installations are completed within 4-6 hours. Larger enterprise or multi-camera projects depend on site complexity and are scheduled as per your convenience."),
            ("Do you support enterprise projects?",
             "Yes. We specialize in enterprise-grade security solutions, including multi-site monitoring, centralized storage, and advanced AI-enabled surveillance."),
        ),
    },
    {
        "id": "warranty",
        "title": "Warranty & Support",
        "icon": "bi-shield-check",
        "items": (
            ("What is the warranty on your products?",
             "Most products come with a 1 to 2-year manufacturer warranty. Specific warranty periods are listed on the technical specifications section of each product page."),
            ("How do I claim a warranty or service?",
             "Simply contact our support team with your order ID. We provide on-site service support for all products installed by our team during the warranty period."),
            ("Is technical support available 24/7?",
             "Yes. Our support desk is available round-the-clock for critical troubleshooting. You can reach us via WhatsApp, phone, or email for instant assistance."),
        ),
    },
)


def faq_page(request):
    sections = []
    number = 0
    for section in FAQ_SECTIONS:
        items = []
        for question, answer in section["items"]:
            number += 1
            items.append({"n": number, "question": question, "answer": answer})
        sections.append({**section, "items": items, "count": len(items)})
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for section in FAQ_SECTIONS for q, a in section["items"]
        ],
    }
    # Escape <, > and & so the JSON can never close the <script> tag early.
    faq_jsonld = (
        json.dumps(faq_schema, ensure_ascii=False)
        .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )
    return render(request, "store/faq.html", {
        "faq_sections": sections,
        "faq_total": number,
        "faq_jsonld": mark_safe(faq_jsonld),
    })


def privacy_policy_page(request):
    return render(request, "store/privacy_policy.html")


def terms_page(request):
    return render(request, "store/terms.html")


def refund_policy_page(request):
    return render(request, "store/refund_policy.html")


def shipping_policy_page(request):
    return render(request, "store/shipping_policy.html")


def compare_page(request):
    return render(request, "store/compare.html")


def validate_compare_products(request):
    """API endpoint to validate if products can be compared (must be from same category)"""
    product_ids = request.GET.getlist('ids', '')
    
    if not product_ids:
        return JsonResponse({"ok": False, "message": "No product IDs provided."}, status=400)
    
    try:
        product_ids = [int(pid) for pid in product_ids if pid.isdigit()]
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "message": "Invalid product IDs."}, status=400)
    
    if not product_ids:
        return JsonResponse({"ok": False, "message": "No valid product IDs provided."}, status=400)
    
    products = Product.objects.filter(id__in=product_ids, is_available=True).values_list('id', 'category_id', 'category__name', 'category__slug').order_by('id')
    
    if not products:
        return JsonResponse({"ok": False, "message": "Products not found."}, status=404)
    
    # Check if all products are from the same category
    categories = set(p[1] for p in products)
    
    if len(categories) > 1:
        category_names = list(set(p[2] for p in products))
        return JsonResponse({
            "ok": False,
            "can_compare": False,
            "message": f"Products must be from the same category. Found products from: {', '.join(category_names)}",
            "products_categories": [{"id": p[0], "category": p[2]} for p in products]
        }, status=400)
    
    # All products are from same category
    category_name = products[0][2]
    category_slug = products[0][3]
    
    return JsonResponse({
        "ok": True,
        "can_compare": True,
        "category": category_name,
        "category_slug": category_slug,
        "product_count": len(products),
        "message": f"All products are from '{category_name}' category. Comparison allowed."
    })


# ─────────────────────────────────────────────
# Wishlist views
# ─────────────────────────────────────────────

@login_required(login_url="login")
def wishlist_page(request):
    """Display all wishlist items for the logged-in user."""
    wishlist_items = (
        Wishlist.objects.filter(user=request.user)
        .select_related("product__category")
    )
    return render(request, "store/wishlist.html", {"wishlist_items": wishlist_items})


@login_required(login_url="login")
@require_POST
def toggle_wishlist(request, product_id):
    """
    Toggle a product in the user's wishlist.
    Returns JSON: {ok, added (bool), wishlist_count}.
    """
    product = get_object_or_404(Product, id=product_id, is_available=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        # Already in wishlist — remove it
        item.delete()
        added = False
    else:
        added = True

    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({
        "ok": True,
        "added": added,
        "wishlist_count": wishlist_count,
        "message": "Added to wishlist." if added else "Removed from wishlist.",
    })


@login_required(login_url="login")
def wishlist_data_api(request):
    """Return JSON of all wishlist items for the logged-in user."""
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    data = []
    for item in items:
        p = item.product
        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image.url if p.image else "",
            "url": reverse("product_detail", args=[p.slug]),
        })
    return JsonResponse({"ok": True, "wishlist": data})
 
