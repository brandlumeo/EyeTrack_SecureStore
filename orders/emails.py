import logging
import threading
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from orders.invoices import build_invoice_bundle
from orders.models import Order
from orders.pdf import build_invoice_pdf


logger = logging.getLogger(__name__)

def _get_admin_recipients():
    admins = getattr(settings, "ADMINS", None) or []
    return [email for _, email in admins if email]


def send_order_placed_email(order_id, base_url=None):
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("user", "shipment")
        .prefetch_related("items__product", "payments")
        .first()
    )
    if not order or not order.email:
        return False

    tracking_url = reverse("order_tracking", args=[order.id])
    if base_url:
        tracking_url = urljoin(base_url, tracking_url.lstrip("/"))
    
    # Add email parameter for guest users
    if not order.user:
        tracking_url += f"?email={order.email}"

    invoice_bundle = build_invoice_bundle(order)
    invoice = invoice_bundle["invoice"]
    
    context = {
        "order": order,
        "invoice_display": invoice_bundle["invoice_display"],
        "tracking_url": tracking_url,
    }

    subject = f"Order placed: Eyetrack Solutions {order.formatted_id}"
    text_body = render_to_string("orders/emails/order_placed_email.txt", context)
    html_body = render_to_string("orders/emails/order_placed_email.html", context)

    admin_recipients = _get_admin_recipients()

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send order placed email for order %s", order_id)
        return False


def send_order_invoice_email(order_id, base_url=None):
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("user", "shipment")
        .prefetch_related("items__product", "payments")
        .first()
    )
    if not order or not order.email:
        return False

    invoice_bundle = build_invoice_bundle(order)
    invoice = invoice_bundle["invoice"]
    if invoice.payment_status != Order.PaymentStatus.PAID:
        return False

    invoice_url = reverse("order_invoice", args=[order.id])
    tracking_url = reverse("order_tracking", args=[order.id])
    if base_url:
        invoice_url = urljoin(base_url, invoice_url.lstrip("/"))
        tracking_url = urljoin(base_url, tracking_url.lstrip("/"))
    
    # Add email parameter for guest users
    if not order.user:
        tracking_url += f"?email={order.email}"

    context = {
        "order": order,
        "invoice": invoice,
        "invoice_display": invoice_bundle["invoice_display"],
        "invoice_url": invoice_url,
        "tracking_url": tracking_url,
    }
    subject = f"Your Eyetrack Solutions order {order.formatted_id} is confirmed"
    text_body = render_to_string("orders/emails/order_invoice_email.txt", context)
    html_body = render_to_string("orders/emails/order_invoice_email.html", context)
    pdf_bytes = build_invoice_pdf(
        invoice,
        order,
        invoice_bundle["invoice_items"],
        invoice_bundle["latest_payment"],
        invoice_bundle["invoice_display"],
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.attach(f"{invoice.invoice_number.lower()}.pdf", pdf_bytes, "application/pdf")
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send invoice email for order %s", order_id)
        return False


def send_admin_order_notification_email(order_id, event_type="placed", base_url=None):
    admin_recipients = _get_admin_recipients()
    if not admin_recipients:
        return False

    order = (
        Order.objects.filter(pk=order_id)
        .select_related("user", "shipment")
        .prefetch_related("items__product", "payments")
        .first()
    )
    if not order:
        return False

    invoice_bundle = build_invoice_bundle(order)
    invoice = invoice_bundle["invoice"]

    context = {
        "order": order,
        "event_type": event_type,
        "invoice_display": invoice_bundle["invoice_display"],
    }

    if event_type == "placed":
        subject = f"[ADMIN] New Order Placed: {order.formatted_id}"
    elif event_type == "cancelled":
        subject = f"[ADMIN] Order Cancelled: {order.formatted_id}"
    else:
        subject = f"[ADMIN] Order Update: {order.formatted_id}"

    text_body = render_to_string("orders/emails/admin_order_notification.txt", context)
    html_body = render_to_string("orders/emails/admin_order_notification.html", context)

    pdf_bytes = None
    if invoice:
        try:
            pdf_bytes = build_invoice_pdf(
                invoice,
                order,
                invoice_bundle["invoice_items"],
                invoice_bundle["latest_payment"],
                invoice_bundle["invoice_display"],
            )
        except Exception:
            logger.exception("Failed to build PDF for admin notification for order %s", order_id)

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_recipients,
        )
        message.attach_alternative(html_body, "text/html")
        
        if pdf_bytes and invoice:
            message.attach(f"{invoice.invoice_number.lower()}.pdf", pdf_bytes, "application/pdf")
            
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send admin notification email for order %s", order_id)
        return False


def send_order_status_update_email(order_id, new_status, base_url=None):
    """
    Send a customer-facing email when an order's status changes.
    Called from the Order post_save signal whenever order_status transitions.

    Covered statuses: CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED.
    PENDING is intentionally excluded (covered by send_order_placed_email).
    """
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("user", "shipment")
        .prefetch_related("items__product", "payments")
        .first()
    )
    if not order or not order.email:
        return False

    # Human-readable label for the email subject/body
    status_labels = {
        Order.OrderStatus.CONFIRMED:   "Confirmed",
        Order.OrderStatus.PROCESSING:  "Being Processed",
        Order.OrderStatus.SHIPPED:     "Shipped",
        Order.OrderStatus.DELIVERED:   "Delivered",
        Order.OrderStatus.CANCELLED:   "Cancelled",
        "out_for_delivery":            "Out for Delivery",
    }
    status_label = status_labels.get(new_status, str(new_status).title())

    tracking_url = reverse("order_tracking", args=[order.id])
    if base_url:
        tracking_url = urljoin(base_url, tracking_url.lstrip("/"))

    shipment = getattr(order, "shipment", None)

    context = {
        "order": order,
        "new_status": new_status,
        "status_label": status_label,
        "tracking_url": tracking_url,
        "shipment": shipment,
    }

    subject = f"Order {order.formatted_id} — {status_label} | Eyetrack Solutions"
    text_body = render_to_string("orders/emails/order_status_update_email.txt", context)
    html_body = render_to_string("orders/emails/order_status_update_email.html", context)

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send status update email for order %s (status=%s)", order_id, new_status)
        return False

def send_payment_reminder_email(order_id, base_url=None):
    """Remind a customer that their online order is waiting for payment (orders.stock / remind_unpaid_orders)."""
    from django.utils import timezone

    from orders.stock import release_deadline

    order = Order.objects.filter(pk=order_id).prefetch_related("items__product").first()
    if not order or not order.email:
        return False
    base_url = base_url or getattr(settings, "SITE_URL", "https://eyetracktechnologies.com/")
    context = {
        "order": order,
        "items": list(order.items.all()),
        "name": order.full_name or "there",
        "pay_url": urljoin(base_url, reverse("razorpay_checkout", args=[order.id]).lstrip("/")),
        "hold_until": timezone.localtime(release_deadline(order)),
        "support_phone": getattr(settings, "BUSINESS_PHONE", "+917994357565"),
    }
    subject = f"Your order {order.formatted_id} is waiting for payment | Eyetrack Solutions"
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=render_to_string("orders/emails/payment_reminder_email.txt", context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        message.attach_alternative(render_to_string("orders/emails/payment_reminder_email.html", context), "text/html")
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send payment reminder for order %s", order_id)
        return False


def send_email_async(func, *args, **kwargs):
    """
    Utility to run email sending functions in a separate thread.
    Ideal for cPanel/Shared hosting where Celery is not available.
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
