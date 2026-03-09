from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Max, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import Order, OrderItem
from .models import Category, Product


def _cart_total_items(cart):
    return sum(cart.values())


def _build_product_specs(product):
    return {
        "camera_type": product.get_camera_type_display() or "-",
        "resolution_mp": f"{product.resolution_mp} MP" if product.resolution_mp else "-",
        "lens_mm": f"{product.lens_mm} mm" if product.lens_mm else "-",
        "field_of_view_deg": f"{product.field_of_view_deg} deg" if product.field_of_view_deg else "-",
        "night_vision_range_m": f"{product.night_vision_range_m} m" if product.night_vision_range_m else "-",
        "frame_rate_fps": f"{product.frame_rate_fps} fps" if product.frame_rate_fps else "-",
        "weatherproof_rating": product.weatherproof_rating or "-",
        "connectivity": product.get_connectivity_display() or "-",
        "power_source": product.get_power_source_display() or "-",
        "storage_support": product.storage_support or "-",
        "audio_support": "Yes" if product.audio_support else "No",
        "ai_detection": "Yes" if product.ai_detection else "No",
        "warranty_years": f"{product.warranty_years} year(s)" if product.warranty_years else "-",
    }


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    products_qs = Product.objects.filter(is_available=True).select_related("category")

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_qs = products_qs.filter(category=category)

    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "featured")
    in_stock = request.GET.get("in_stock")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if in_stock == "1":
        products_qs = products_qs.filter(stock__gt=0)

    if min_price:
        products_qs = products_qs.filter(price__gte=min_price)
    if max_price:
        products_qs = products_qs.filter(price__lte=max_price)

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

    products = products_qs
    featured_products = Product.objects.filter(is_available=True, stock__gt=0).order_by("-stock", "-created_at")[:4]
    top_sellers = Product.objects.filter(is_available=True).order_by("-created_at")[:6]
    price_range = Product.objects.filter(is_available=True).aggregate(min_price=Min("price"), max_price=Max("price"))

    context = {
        "category": category,
        "categories": categories,
        "products": products,
        "featured_products": featured_products,
        "top_sellers": top_sellers,
        "result_count": products.count(),
        "q": query,
        "sort": sort,
        "in_stock": in_stock == "1",
        "min_price": min_price or "",
        "max_price": max_price or "",
        "min_catalog_price": price_range["min_price"] or 0,
        "max_catalog_price": price_range["max_price"] or 0,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_available=True)
    related_products = (
        Product.objects.filter(category=product.category, is_available=True)
        .exclude(id=product.id)
        .order_by("-created_at")[:4]
    )

    specs = []
    if product.ai_detection:
        specs.append("AI Detection")
    if product.night_vision_range_m:
        specs.append(f"Night Vision {product.night_vision_range_m}m")
    if product.weatherproof_rating:
        specs.append(product.weatherproof_rating)
    if product.connectivity:
        specs.append(product.get_connectivity_display())
    if product.resolution_mp:
        specs.append(f"{product.resolution_mp}MP")
    if not specs:
        specs = ["Professional CCTV Build"]

    context = {
        "product": product,
        "related_products": related_products,
        "specs": specs,
        "product_specs": _build_product_specs(product),
    }
    return render(request, "store/product_detail.html", context)


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
            "description": product.description,
            "image": product.image.url if product.image else "",
            "specs": _build_product_specs(product),
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
    product_id = str(product_id)
    current_qty = cart.get(product_id, 0)
    if current_qty >= product.stock:
        msg = f"Only {product.stock} unit(s) available for this item."
        if wants_json:
            return JsonResponse({"ok": False, "message": msg}, status=400)
        messages.warning(request, msg)
        return redirect(next_url)

    cart[product_id] = current_qty + 1
    request.session["cart"] = cart
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
                    "quantity": cart[product_id],
                    "slug": product.slug,
                    "image": product.image.url if product.image else "",
                },
                "cart_url": reverse("cart"),
            }
        )
    messages.success(request, msg)
    return redirect(next_url)


def cart_view(request):
    cart = request.session.get("cart", {})
    products = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, is_available=True).first()
        if not product:
            continue
        product.quantity = quantity
        product.subtotal = product.price * quantity
        total += product.subtotal
        products.append(product)

    shipping = Decimal("0.00") if total >= Decimal("5000.00") else Decimal("299.00")
    tax = total * Decimal("0.18")
    grand_total = total + shipping + tax
    recommended_products = Product.objects.filter(is_available=True, stock__gt=0).exclude(
        id__in=[item.id for item in products]
    )[:4]

    context = {
        "products": products,
        "total": total,
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
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session["cart"] = cart
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
    request.session["cart"] = cart
    return redirect(next_url)


@login_required(login_url="login")
def checkout(request):
    cart = request.session.get("cart", {})
    if not cart:
        return redirect("product_list")

    product_quantities = {int(pid): qty for pid, qty in cart.items() if qty > 0}
    if not product_quantities:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    products = []
    subtotal_total = Decimal("0.00")
    for product_id, quantity in product_quantities.items():
        product = get_object_or_404(Product, id=product_id, is_available=True)
        subtotal = product.price * quantity
        subtotal_total += subtotal
        products.append({"product": product, "quantity": quantity, "subtotal": subtotal})

    shipping = Decimal("0.00") if subtotal_total >= Decimal("5000.00") else Decimal("299.00")
    tax = subtotal_total * Decimal("0.18")
    grand_total = subtotal_total + shipping + tax

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        if not all([full_name, email, phone, address]):
            messages.error(request, "Please fill in all required checkout fields.")
        else:
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

                locked_shipping = Decimal("0.00") if recalculated_subtotal >= Decimal("5000.00") else Decimal("299.00")
                locked_tax = recalculated_subtotal * Decimal("0.18")
                locked_grand_total = recalculated_subtotal + locked_shipping + locked_tax

                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    total=locked_grand_total,
                    status="Pending",
                )
                for product_id, quantity in product_quantities.items():
                    product_instance = locked_map[product_id]
                    OrderItem.objects.create(
                        order=order,
                        product=product_instance,
                        quantity=quantity,
                        price=product_instance.price,
                    )
            return redirect("simulated_payment", order_id=order.id)

    context = {
        "products": products,
        "total": subtotal_total,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/checkout.html", context)


def order_success(request):
    latest_order = None
    if request.user.is_authenticated:
        latest_order = request.user.orders.order_by("-created_at").first()
    return render(request, "store/order_success.html", {"latest_order": latest_order})


@login_required(login_url="login")
def simulated_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != "Pending":
        return redirect("order_history")

    if request.method == "POST":
        with transaction.atomic():
            locked_order = get_object_or_404(Order.objects.select_for_update(), id=order_id, user=request.user)
            if locked_order.status != "Pending":
                messages.info(request, "This order has already been processed.")
                return redirect("order_history")

            item_product_ids = list(locked_order.items.values_list("product_id", flat=True))
            locked_products = Product.objects.select_for_update().filter(id__in=item_product_ids)
            product_map = {product.id: product for product in locked_products}

            for item in locked_order.items.select_related("product"):
                locked_product = product_map.get(item.product_id)
                if not locked_product or locked_product.stock < item.quantity:
                    available = locked_product.stock if locked_product else 0
                    messages.error(
                        request,
                        f"Stock changed for {item.product.name}. Available: {available}, required: {item.quantity}.",
                    )
                    return redirect("cart")

            for item in locked_order.items.select_related("product"):
                locked_product = product_map[item.product_id]
                locked_product.stock -= item.quantity
                locked_product.save()

            locked_order.status = "Completed"
            locked_order.save(update_fields=["status"])

        request.session["cart"] = {}
        return redirect("order_success")

    return render(request, "store/payment.html", {"order": order})


def about_page(request):
    return render(request, "store/about.html")


def services_page(request):
    return render(request, "store/services.html")


def support_page(request):
    return render(request, "store/support.html")


def faq_page(request):
    return render(request, "store/faq.html")


def privacy_policy_page(request):
    return render(request, "store/privacy_policy.html")


def terms_page(request):
    return render(request, "store/terms.html")


def refund_policy_page(request):
    return render(request, "store/refund_policy.html")


def shipping_policy_page(request):
    return render(request, "store/shipping_policy.html")


def wishlist_page(request):
    return render(request, "store/wishlist.html")


def compare_page(request):
    return render(request, "store/compare.html")
