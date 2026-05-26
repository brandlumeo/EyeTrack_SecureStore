import logging
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from orders.invoices import build_invoice_bundle
from orders.models import Invoice, Order, Shipment
from orders.pdf import build_invoice_pdf
from config.firebase_setup import initialize_firebase, is_firebase_ready

from .forms import AddressForm, EmailOrUsernameAuthenticationForm, ProfileForm, RegistrationForm, ResendVerificationForm
from .models import Address, Profile

try:
    from firebase_admin import auth as firebase_auth
except ModuleNotFoundError:
    firebase_auth = None


logger = logging.getLogger(__name__)


def _firebase_auth_unavailable_response(message, *, ok_key="ok"):
    logger.warning("Firebase auth requested but firebase_admin is unavailable or not initialized.")
    return JsonResponse({ok_key: False, "message": message}, status=503)


def build_shipping_tracker(order, shipment):
    steps = [
        {"value": Order.ShippingStatus.NOT_SHIPPED, "label": "Not Shipped"},
        {"value": Order.ShippingStatus.PACKED, "label": "Packed"},
        {"value": Order.ShippingStatus.IN_TRANSIT, "label": "In Transit"},
        {"value": Order.ShippingStatus.OUT_FOR_DELIVERY, "label": "Out For Delivery"},
        {"value": Order.ShippingStatus.DELIVERED, "label": "Delivered"},
    ]
    current_value = order.shipping_status or Order.ShippingStatus.NOT_SHIPPED

    # Ensure UI consistency: If overall order status is Delivered, the timeline must show Delivered.
    if order.order_status == Order.OrderStatus.DELIVERED:
        current_value = Order.ShippingStatus.DELIVERED

    current_index = next(
        (index for index, step in enumerate(steps) if step["value"] == current_value),
        0,
    )
    progress_copy = {
        Order.ShippingStatus.NOT_SHIPPED: "Your order is confirmed and waiting for dispatch.",
        Order.ShippingStatus.PACKED: "Your package has been packed and is being prepared for handoff.",
        Order.ShippingStatus.IN_TRANSIT: "Your shipment is moving through the courier network.",
        Order.ShippingStatus.OUT_FOR_DELIVERY: "Your package is out for delivery and should arrive soon.",
        Order.ShippingStatus.DELIVERED: "Your package has been delivered.",
    }
    step_rows = []
    for index, step in enumerate(steps):
        state = "upcoming"
        if index < current_index:
            state = "complete"
        elif index == current_index:
            state = "current"
        step_rows.append({**step, "state": state})

    return {
        "order": order,
        "shipment": shipment,
        "headline": progress_copy.get(current_value, progress_copy[Order.ShippingStatus.NOT_SHIPPED]),
        "steps": step_rows,
    }


def build_installation_tracker(order):
    from orders.models import InstallationBooking
    try:
        booking = order.installation_booking
    except Exception:
        return None

    steps = [
        {"value": InstallationBooking.BookingStatus.PENDING, "label": "Pending Confirmation"},
        {"value": InstallationBooking.BookingStatus.ASSIGNED, "label": "Technician Assigned"},
        {"value": InstallationBooking.BookingStatus.ON_SITE, "label": "On-Site / In-Progress"},
        {"value": InstallationBooking.BookingStatus.COMPLETED, "label": "Installation Completed"},
    ]
    
    current_value = booking.status
    
    # Handle legacy 'scheduled' status if it exists in DB still
    if current_value == "scheduled":
        current_value = InstallationBooking.BookingStatus.ASSIGNED

    current_index = next(
        (index for index, step in enumerate(steps) if step["value"] == current_value),
        0,
    )

    progress_copy = {
        InstallationBooking.BookingStatus.PENDING: "Your request is received. We are verifying availability for your preferred slot.",
        InstallationBooking.BookingStatus.ASSIGNED: f"Expert technician {booking.technician_name} has been assigned to your order.",
        InstallationBooking.BookingStatus.ON_SITE: "The technician is at your location and the installation is in progress.",
        InstallationBooking.BookingStatus.COMPLETED: "Installation successfully completed. Enjoy your secure environment!",
    }

    step_rows = []
    for index, step in enumerate(steps):
        state = "upcoming"
        if index < current_index:
            state = "complete"
        elif index == current_index:
            state = "current"
        step_rows.append({**step, "state": state})

    return {
        "booking": booking,
        "headline": progress_copy.get(current_value, progress_copy[InstallationBooking.BookingStatus.PENDING]),
        "steps": step_rows,
    }


def _format_customer_name(value):
    words = str(value or "").split()
    if not words:
        return "Customer"

    formatted_words = []
    for word in words:
        if word.islower() or word.isupper():
            formatted_words.append(word.capitalize())
        else:
            formatted_words.append(word)
    return " ".join(formatted_words)


def _format_address(value):
    segments = []
    for line in str(value or "").splitlines():
        for segment in line.split(","):
            cleaned = " ".join(segment.split())
            if cleaned:
                segments.append(cleaned)
    return ", ".join(segments) or "Address not available"


def _get_payment_label(order, payment):
    if payment:
        return payment.get_status_display()
    return order.get_payment_status_display()


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def build_account_context(user):
    profile = get_profile(user)
    orders = Order.objects.filter(user=user)
    return {
        "account_profile": profile,
        "account_addresses_count": user.addresses.count(),
        "account_orders_count": orders.count(),
        "account_latest_order": orders.order_by("-created_at").first(),
    }


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verify_url = request.build_absolute_uri(reverse("verify_email", args=[uid, token]))
    subject = "Verify your Eyetrack Solutions account"
    message = render_to_string("accounts/verification_email.txt", {"user": user, "verify_url": verify_url})
    
    # Use transaction.on_commit for safety, but send directly
    transaction.on_commit(lambda: user.email_user(subject, message))


@require_POST
def firebase_verify_phone(request):
    """
    Verifies a Firebase ID Token received from the frontend after successful phone auth.
    Supports both logged-in users and guest users (for registration).
    """
    if firebase_auth is None:
        return _firebase_auth_unavailable_response("Phone verification is unavailable right now.")
    if not is_firebase_ready() and not initialize_firebase():
        logger.error("Firebase phone verification requested but Firebase Admin SDK is not ready.")
        return _firebase_auth_unavailable_response("Phone verification is unavailable right now.")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)
        
    id_token = data.get("id_token")
    if not id_token:
        return JsonResponse({"ok": False, "message": "No token provided"}, status=400)
        
    try:
        # Verify the ID token using firebase_admin
        decoded_token = firebase_auth.verify_id_token(id_token)
        phone_number = decoded_token.get("phone_number")
        
        if not phone_number:
            return JsonResponse({"ok": False, "message": "Token does not contain a phone number"}, status=400)
            
        if request.user.is_authenticated:
            # Update the logged-in user's profile
            profile = get_profile(request.user)
            profile.phone_number = phone_number
            profile.phone_verified = True
            profile.save(update_fields=["phone_number", "phone_verified"])
            logger.info(f"User {request.user.email} successfully verified phone {phone_number} via Firebase.")
        else:
            # Store in session for registration flow
            request.session["phone_verified_in_session"] = True
            request.session["verified_phone_number"] = phone_number
            request.session.modified = True
            logger.info(f"Guest session successfully verified phone {phone_number} via Firebase.")
        
        return JsonResponse({
            "ok": True, 
            "message": "Phone number verified successfully!",
            "phone": phone_number
        })
        
    except Exception as e:
        logger.error(f"Firebase phone verification failed: {str(e)}")
        return JsonResponse({"ok": False, "message": "Invalid or expired token"}, status=400)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("account_dashboard")

    form = RegistrationForm(request.POST or None)
    inactive_email = ""
    if request.method == "POST":
        submitted_email = request.POST.get("email", "").strip().lower()
        if submitted_email and User.objects.filter(email__iexact=submitted_email, is_active=False).exists():
            inactive_email = submitted_email
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    from accounts.models import Notification
                    Notification.send(
                        user=user,
                        title="Welcome to EyeTrack!",
                        message="Your account has been created successfully. Be sure to verify your email.",
                        notification_type=Notification.NotificationType.ALERT,
                    )
                    send_verification_email(request, user)
            except Exception:
                logger.exception(
                    "Failed to send verification email during registration for %s",
                    form.cleaned_data.get("email", ""),
                )
                messages.error(
                    request,
                    "We could not send the verification email right now. Check the email configuration and try again.",
                )
                return render(request, "accounts/register.html", {"form": form, "inactive_email": inactive_email})
            
            request.session["pending_verification_email"] = user.email
            messages.success(request, "Account created successfully. Check your email to verify and activate your account.")
            return redirect("verify_email_sent")
        messages.error(request, "Please correct the highlighted registration errors and try again.")
    return render(request, "accounts/register.html", {"form": form, "inactive_email": inactive_email})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("account_dashboard")

    next_url = request.GET.get("next") or request.POST.get("next")
    form = EmailOrUsernameAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Login successful.")
            return redirect(next_url or "product_list")
        messages.error(request, "Unable to sign you in. Check your credentials and try again.")
    return render(request, "accounts/login.html", {"form": form, "next": next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("product_list")


def verify_email_sent(request):
    return render(
        request,
        "accounts/verify_email_sent.html",
        {"email": request.session.get("pending_verification_email")},
    )


def resend_verification_email_view(request):
    initial_email = request.GET.get("email", "").strip().lower()
    form = ResendVerificationForm(
        request.POST or None,
        initial={"email": initial_email} if initial_email and request.method != "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.info(request, "If an inactive account exists for that email, a new verification link has been sent.")
            request.session["pending_verification_email"] = email
            return redirect("verify_email_sent")
        if user.is_active:
            messages.info(request, "This email is already verified. Please sign in.")
            return redirect("login")

        try:
            send_verification_email(request, user)
        except Exception:
            logger.exception("Failed to resend verification email for %s", email)
            messages.error(
                request,
                "We could not send the verification email right now. Check the email configuration and try again.",
            )
        else:
            request.session["pending_verification_email"] = user.email
            messages.success(request, "A fresh verification link has been sent to your email.")
            return redirect("verify_email_sent")

    return render(request, "accounts/resend_verification.html", {"form": form})


def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        profile = get_profile(user)
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        messages.success(request, "Email verified. You can now sign in.")
        return redirect("login")

    messages.error(request, "This verification link is invalid or expired.")
    return redirect("register")


@login_required(login_url="login")
def account_dashboard(request):
    context = build_account_context(request.user)
    context.update(
        {
            "default_address": request.user.addresses.filter(is_default=True).first(),
            "recent_orders": Order.objects.filter(user=request.user).order_by("-created_at")[:3],
        }
    )
    return render(request, "accounts/dashboard.html", context)


@login_required(login_url="login")
def profile_view(request):
    profile = get_profile(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    
    if request.method == "POST" and form.is_valid():
        original_email = request.user.email
        
        try:
            with transaction.atomic():
                updated_profile = form.save()
                
                # Handle email verification status
                if updated_profile.user.email.lower() != original_email.lower():
                    updated_profile.email_verified = False
                    updated_profile.save(update_fields=["email_verified"])
                    updated_profile.user.is_active = False
                    updated_profile.user.save(update_fields=["is_active"])
                    send_verification_email(request, updated_profile.user)
        except Exception:
            logger.exception(
                "Failed to send verification email after profile email change for user %s",
                request.user.pk,
            )
            request.user.refresh_from_db()
            profile.refresh_from_db()
            form = ProfileForm(instance=profile, user=request.user)
            messages.error(
                request,
                "We could not send the verification email to your new address. Your account details were not changed.",
            )
            context = build_account_context(request.user)
            context.update({"form": form})
            return render(request, "accounts/profile.html", context)

        if updated_profile.user.email.lower() != original_email.lower():
            logout(request)
            messages.info(request, "Email changed. Please verify your new email before signing in again.")
            return redirect("verify_email_sent")
        
        messages.success(request, "Account settings updated.")
        return redirect("profile")

    context = build_account_context(request.user)
    context.update({"form": form, "profile": profile})
    return render(request, "accounts/profile.html", context)


@login_required(login_url="login")
def address_list_view(request):
    context = build_account_context(request.user)
    context.update({"addresses": request.user.addresses.all()})
    return render(request, "accounts/address_list.html", context)


@login_required(login_url="login")
def address_create_view(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, "Address added.")
        return redirect("address_list")

    context = build_account_context(request.user)
    context.update({"form": form, "page_title": "Add Address"})
    return render(request, "accounts/address_form.html", context)


@login_required(login_url="login")
def address_update_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Address updated.")
        return redirect("address_list")

    context = build_account_context(request.user)
    context.update({"form": form, "page_title": "Edit Address", "address": address})
    return render(request, "accounts/address_form.html", context)


@login_required(login_url="login")
@require_POST
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address removed.")
    return redirect("address_list")


@login_required(login_url="login")
@require_POST
def address_set_default_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Default shipping address updated.")
    return redirect("address_list")


@login_required(login_url="login")
def order_history(request):
    orders_qs = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product", "shipment", "installation_booking")
        .order_by("-created_at")
    )
    order_summary = orders_qs.aggregate(total_orders=Count("id"), total_spend=Sum("total"))
    status_counts = {
        "pending": orders_qs.filter(order_status=Order.OrderStatus.PENDING).count(),
        "confirmed": orders_qs.filter(order_status=Order.OrderStatus.CONFIRMED).count(),
        "processing": orders_qs.filter(order_status=Order.OrderStatus.PROCESSING).count(),
        "shipped": orders_qs.filter(order_status=Order.OrderStatus.SHIPPED).count(),
        "delivered": orders_qs.filter(order_status=Order.OrderStatus.DELIVERED).count(),
        "cancelled": orders_qs.filter(order_status=Order.OrderStatus.CANCELLED).count(),
        "returned": orders_qs.filter(order_status=Order.OrderStatus.RETURNED).count(),
    }
    orders = list(orders_qs)
    order_rows = []
    for order in orders:
        try:
            shipment = order.shipment
        except Shipment.DoesNotExist:
            shipment = None
        order_rows.append({"order": order, "shipment": shipment})
    context = build_account_context(request.user)
    context.update(
        {
            "orders": orders,
            "order_rows": order_rows,
            "order_summary": order_summary,
            "status_counts": status_counts,
            "latest_order": orders[0] if orders else None,
        }
    )
    return render(request, "accounts/order_history.html", context)


def order_tracking(request, pk):
    # Try to get order for logged-in user or guest
    if request.user.is_authenticated:
        # Logged-in user: get their orders or guest orders matching their email
        order = get_object_or_404(
            Order.objects.filter(Q(user=request.user) | Q(user__isnull=True, email__iexact=request.user.email))
            .select_related("shipment")
            .prefetch_related("items__product", "payments"),
            pk=pk,
        )
    else:
        # Guest user: get order by email if provided in GET params
        email = request.GET.get('email', '').strip()
        if not email:
            messages.error(request, "Please log in to track your order, or provide your email address.")
            from django.urls import reverse
            from urllib.parse import urlencode
            login_url = reverse("login")
            query_string = urlencode({'next': request.path})
            return redirect(f"{login_url}?{query_string}")
        
        order = get_object_or_404(
            Order.objects.filter(user__isnull=True, email__iexact=email)
            .select_related("shipment")
            .prefetch_related("items__product", "payments"),
            pk=pk,
        )
    shipment = getattr(order, "shipment", None)
    tracking_focus = build_shipping_tracker(order, shipment)
    installation_focus = build_installation_tracker(order)
    latest_payment = order.payments.order_by("-created_at").first()
    tracked_items = list(order.items.all())
    for item in tracked_items:
        item.line_total = item.price * item.quantity
    tracking_display = {
        "recipient_name": _format_customer_name(order.full_name),
        "address": _format_address(order.address),
        "payment_status": _get_payment_label(order, latest_payment),
        "tracking_number": order.tracking_number or "Not assigned yet",
        "carrier": shipment.carrier.strip() if shipment and shipment.carrier.strip() else "To be assigned",
        "service_level": shipment.service_level.strip() if shipment and shipment.service_level.strip() else "Standard",
    }

    context = build_account_context(request.user)
    context.update(
        {
            "tracked_order": order,
            "tracked_shipment": shipment,
            "tracking_focus": tracking_focus,
            "installation_focus": installation_focus,
            "latest_payment": latest_payment,
            "tracked_items": tracked_items,
            "tracking_display": tracking_display,
            "order_is_returnable": order.is_returnable,
            "return_requests": order.return_requests.all(),
        }
    )
    return render(request, "accounts/order_tracking.html", context)


@login_required(login_url="login")
def order_return(request, pk):
    """
    Submits a return request for a delivered order within a 15-day window.
    """
    from orders.models import ReturnRequest, ReturnItem, ReturnPhoto, OrderItem
    
    order = get_object_or_404(Order.objects.filter(user=request.user), pk=pk)
    
    # Validation: Must be delivered and within 15 days
    if not order.is_returnable:
        messages.error(request, "This order is not eligible for return. Ensure it was delivered within the last 15 days.")
        return redirect("order_tracking", pk=order.pk)
    
    # Check if a pending or active return already exists
    active_returns = order.return_requests.exclude(status=ReturnRequest.ReturnStatus.REJECTED).exists()
    if active_returns:
        messages.info(request, "A return request is already active for this order.")
        return redirect("order_tracking", pk=order.pk)

    if request.method == "POST":
        reason = request.POST.get("reason")
        details = request.POST.get("details")
        item_ids = request.POST.getlist("items") # list of order_item ids
        photos = request.FILES.getlist("photos")
        
        if not item_ids:
            messages.error(request, "Please select at least one item to return.")
            return redirect("order_return", pk=order.pk)
            
        try:
            with transaction.atomic():
                return_request = ReturnRequest.objects.create(
                    order=order,
                    user=request.user,
                    reason=reason,
                    details=details
                )
                
                # Attach items
                for item_id in item_ids:
                    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                    qty = request.POST.get(f"qty_{item_id}", order_item.quantity)
                    ReturnItem.objects.create(
                        return_request=return_request,
                        order_item=order_item,
                        quantity=int(qty)
                    )
                
                # Attach photos
                for photo in photos:
                    ReturnPhoto.objects.create(return_request=return_request, image=photo)
                
                # Send Notification
                from .models import Notification
                Notification.send(
                    user=request.user,
                    title="Return Request Received",
                    message=f"Your return request for Order {order.formatted_id} has been received and is under review.",
                    notification_type=Notification.NotificationType.ORDER,
                    link=f"/accounts/orders/{order.id}/track/"
                )
                
                messages.success(request, "Your return request has been submitted successfully. Our team will review it shortly.")
                return redirect("order_tracking", pk=order.pk)
                
        except Exception as e:
            logger.exception("Failed to process return request for order %s", order.id)
            messages.error(request, f"An error occurred while processing your return. Please try again.")
            return redirect("order_return", pk=order.pk)

    context = build_account_context(request.user)
    context.update({
        "order": order,
        "items": order.items.select_related("product").all(),
        "reasons": ReturnRequest.ReturnReason.choices
    })
    return render(request, "accounts/return_request_form.html", context)


@login_required(login_url="login")
def order_invoice(request, pk):
    order = get_object_or_404(
        Order.objects.filter(Q(user=request.user) | Q(user__isnull=True, email__iexact=request.user.email))
        .select_related("shipment")
        .prefetch_related("items__product", "payments"),
        pk=pk,
    )
    
    if order.order_status not in [Order.OrderStatus.SHIPPED, Order.OrderStatus.DELIVERED]:
        messages.info(request, "Invoice will be available for download once the order has been shipped.")
        return redirect("order_history")
        
    invoice_bundle = build_invoice_bundle(order)
    context = build_account_context(request.user)
    context.update(
        {
            "invoiced_order": order,
            **invoice_bundle,
        }
    )
    return render(request, "accounts/order_invoice.html", context)


@login_required(login_url="login")
def order_invoice_download(request, pk):
    order = get_object_or_404(
        Order.objects.filter(Q(user=request.user) | Q(user__isnull=True, email__iexact=request.user.email))
        .prefetch_related("items__product", "payments"),
        pk=pk,
    )
    
    if order.order_status not in [Order.OrderStatus.SHIPPED, Order.OrderStatus.DELIVERED]:
        messages.info(request, "Invoice will be available for download once the order has been shipped.")
        return redirect("order_history")
        
    invoice_bundle = build_invoice_bundle(order)
    pdf_bytes = build_invoice_pdf(
        invoice_bundle["invoice"],
        order,
        invoice_bundle["invoice_items"],
        invoice_bundle["latest_payment"],
        invoice_bundle["invoice_display"],
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice_bundle["invoice"].invoice_number.lower()}.pdf"'
    )
    return response


@login_required(login_url="login")
@require_POST
def cancel_order(request, pk):
    """
    Allow a customer to cancel their own order.
    Only PENDING and CONFIRMED orders are cancellable —
    once it's PROCESSING, SHIPPED or DELIVERED, customers must contact support.
    Stock is restored atomically when the order is cancelled.
    """
    from store.models import Product

    order = get_object_or_404(
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product"),
        pk=pk,
    )

    # Cancellable statuses
    cancellable = {Order.OrderStatus.PENDING, Order.OrderStatus.CONFIRMED}
    if order.order_status not in cancellable:
        messages.error(
            request,
            f"Order {order.formatted_id} can no longer be cancelled "
            f"(current status: {order.get_order_status_display()}). "
            "Please contact support if you need help."
        )
        return redirect("order_tracking", pk=order.id)

    with transaction.atomic():
        # Restore stock for each item
        for item in order.items.select_related("product").all():
            if item.product:
                Product.objects.filter(pk=item.product.pk).update(
                    stock=F("stock") + item.quantity
                )

        order.order_status = Order.OrderStatus.CANCELLED
        order.save(update_fields=["order_status", "updated_at"])

    messages.success(
        request,
        f"Order {order.formatted_id} has been cancelled. "
        "Your stock will be restored. "
        "If you paid online, you'll be refunded within 5-7 business days."
    )
    return redirect("order_tracking", pk=order.id)


@login_required
@require_POST
def save_fcm_token(request):
    try:
        data = json.loads(request.body)
        token = data.get('fcm_token')
        if token:
            profile = get_profile(request.user)
            profile.fcm_token = token
            profile.save(update_fields=['fcm_token'])
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Token missing'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
def google_gsi_login(request):
    """
    Verifies a Google Identity Services (GSI) credential token.
    Uses Google's tokeninfo API — no Firebase JS SDK, no popups, no COOP issues.
    """
    import urllib.request
    import urllib.error

    try:
        # Handle both JSON (fetch/popup) and Form Data (redirect)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                credential = data.get("credential")
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "message": "Invalid JSON request."}, status=400)
        else:
            credential = request.POST.get("credential")

        if not credential:
            if request.content_type == 'application/json':
                return JsonResponse({"success": False, "message": "No credential provided."}, status=400)
            else:
                messages.error(request, "Google authentication failed. No credential received.")
                return redirect("login")

        # Verify token with Google's tokeninfo endpoint
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                token_data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            logger.warning("Google tokeninfo verification failed: %s", e)
            if request.content_type == 'application/json':
                return JsonResponse({"success": False, "message": "Invalid Google credential."}, status=401)
            else:
                messages.error(request, "Invalid Google credential.")
                return redirect("login")
        except Exception as e:
            logger.error("Google tokeninfo request error: %s", e)
            if request.content_type == 'application/json':
                return JsonResponse({"success": False, "message": "Could not verify credential. Try again."}, status=500)
            else:
                messages.error(request, "Could not verify Google credential. Please try again.")
                return redirect("login")

        email = token_data.get("email")
        email_verified = token_data.get("email_verified") == "true"
        given_name = token_data.get("given_name", "")
        family_name = token_data.get("family_name", "")
        full_name = token_data.get("name", "")
        sub = token_data.get("sub")  # Google's unique user ID

        if not email:
            return JsonResponse({"success": False, "message": "No email in Google credential."})

        if not given_name and full_name:
            parts = full_name.split(" ", 1)
            given_name = parts[0]
            family_name = parts[1] if len(parts) > 1 else ""

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            created = False

            if not user:
                username = email.split('@')[0]
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{get_random_string(4)}"
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=get_random_string(16),
                    first_name=given_name[:150],
                    last_name=family_name[:150],
                    is_active=True,
                )
                created = True

                profile = get_profile(user)
                profile.email_verified = email_verified
                profile.save()

                from accounts.models import Notification
                Notification.send(
                    user=user,
                    title="Welcome to EyeTrack!",
                    message="Your account has been created successfully via Google.",
                    notification_type=Notification.NotificationType.ALERT,
                )
                logger.info("New user created via GSI: %s", email)
            else:
                # Update name if it was empty
                if not user.first_name and given_name:
                    user.first_name = given_name[:150]
                    user.last_name = family_name[:150]
                    user.save(update_fields=["first_name", "last_name"])

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        logger.info("GSI login success: %s (created=%s)", email, created)
        
        if request.content_type == 'application/json':
            return JsonResponse({"success": True, "created": created})
        else:
            if created:
                messages.success(request, "Welcome to EyeTrack! Your account has been created via Google.")
            else:
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect("account_dashboard")

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)
    except Exception as e:
        logger.exception("Unexpected error in google_gsi_login: %s", e)
        if request.content_type == 'application/json':
            return JsonResponse({"success": False, "message": "An unexpected error occurred."}, status=500)
        else:
            messages.error(request, "An unexpected error occurred during Google login.")
            return redirect("login")


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile

@require_POST
def firebase_login(request):
    if firebase_auth is None:
        return _firebase_auth_unavailable_response(
            "Firebase login is unavailable right now.",
            ok_key="success",
        )
    if not is_firebase_ready() and not initialize_firebase():
        logger.error("Firebase login requested but Firebase Admin SDK is not ready.")
        return _firebase_auth_unavailable_response(
            "Server authentication configuration error. Please contact support.",
            ok_key="success",
        )

    try:
        data = json.loads(request.body)
        id_token = data.get("id_token")
        login_method = data.get("login_method", "google")
        
        if not id_token:
            return JsonResponse({"success": False, "message": "No token provided."}, status=400)
        
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        phone_number = decoded_token.get("phone_number")
        
        user = None
        created = False
        
        with transaction.atomic():
            if login_method == "google":
                if not email:
                    return JsonResponse({"success": False, "message": "No email associated with this Google account."})
                user = User.objects.filter(email__iexact=email).first()
                if not user:
                    username = email.split('@')[0]
                    if User.objects.filter(username=username).exists():
                        username = f"{username}_{get_random_string(4)}"
                    user = User.objects.create_user(username=username, email=email, password=get_random_string(16))
                    
                    given_name = decoded_token.get("given_name", "")
                    family_name = decoded_token.get("family_name", "")
                    if not given_name and decoded_token.get("name"):
                        name_parts = decoded_token.get("name").split(" ", 1)
                        given_name = name_parts[0]
                        if len(name_parts) > 1:
                            family_name = name_parts[1]
                    
                    user.first_name = given_name[:150]
                    user.last_name = family_name[:150]
                    user.is_active = True
                    user.save()
                    created = True
                    
                    profile = get_profile(user)
                    profile.email_verified = decoded_token.get("email_verified", False)
                    profile.save()
                    
                    from accounts.models import Notification
                    Notification.send(
                        user=user,
                        title="Welcome to EyeTrack!",
                        message="Your account has been created successfully via Google.",
                        notification_type=Notification.NotificationType.ALERT,
                    )
                    
            elif login_method == "phone":
                if not phone_number:
                    return JsonResponse({"success": False, "message": "No phone number resolved."})
                profile = Profile.objects.filter(phone_number=phone_number).first()
                if profile:
                    user = profile.user
                else:
                    placeholder_email = f"phone_{uid}@eyetrack.local"
                    username = f"user_{get_random_string(8)}"
                    user = User.objects.create_user(username=username, email=placeholder_email, password=get_random_string(16))
                    user.is_active = True
                    user.save()
                    created = True
                    
                    new_profile = get_profile(user)
                    new_profile.phone_number = phone_number
                    new_profile.phone_verified = True
                    new_profile.save()
            
            if user:
                login(request, user)
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "message": "Authentication logic failed."})
                
    except Exception as e:
        if firebase_auth is not None and isinstance(e, firebase_auth.InvalidIdTokenError):
            return JsonResponse({"success": False, "message": "Invalid authentication token from Firebase."})
        logger.exception("Firebase login internal failure")
        return JsonResponse({"success": False, "message": "Internal error occurred."})

@login_required
def notifications_api(request):
    """Returns unread count and latest 10 notifications."""
    from .models import Notification
    
    notifications = Notification.objects.filter(user=request.user)[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    html = render_to_string("accounts/includes/notification_list.html", {
        "notifications": notifications
    }, request=request)
    
    return JsonResponse({
        "unread_count": unread_count,
        "html": html
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    from .models import Notification
    try:
        data = json.loads(request.body)
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return JsonResponse({"success": True})
    except (Notification.DoesNotExist, json.JSONDecodeError):
        return JsonResponse({"success": False}, status=400)

@login_required
@require_POST
def clear_notifications(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})
