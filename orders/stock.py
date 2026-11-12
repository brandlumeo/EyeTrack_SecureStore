"""Stock held by orders.

Checkout takes stock when an order is created, for every payment method. An online order that is never
paid would hold that stock forever, so unpaid online orders are released after UNPAID_ORDER_HOLD_HOURS:
cancelled quietly (no emails or pushes) and their stock returned by the cancellation signal.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from store.models import Product

from .models import Order

logger = logging.getLogger(__name__)

DEFAULT_HOLD_HOURS = 24
DEFAULT_REMINDER_HOURS = 2


def hold_hours():
    return getattr(settings, "UNPAID_ORDER_HOLD_HOURS", DEFAULT_HOLD_HOURS)


def reminder_hours():
    return getattr(settings, "UNPAID_ORDER_REMINDER_HOURS", DEFAULT_REMINDER_HOURS)


def release_deadline(order):
    return order.created_at + timedelta(hours=hold_hours())


def _unpaid_online():
    return Order.objects.filter(
        payment_method=Order.PaymentMethod.ONLINE,
        payment_status=Order.PaymentStatus.PENDING,
        order_status=Order.OrderStatus.PENDING,
    )


def expired_unpaid_orders(older_than_hours=None):
    hours = hold_hours() if older_than_hours is None else older_than_hours
    return _unpaid_online().filter(created_at__lt=timezone.now() - timedelta(hours=hours)).order_by("created_at")


def orders_due_reminder():
    """Unpaid online orders from customer accounts, past the reminder time, not yet reminded,
    and with at least an hour left before they are released (guest orders can't pay from an email link)."""
    now = timezone.now()
    return _unpaid_online().filter(
        user__isnull=False,
        payment_reminder_sent_at__isnull=True,
        created_at__lte=now - timedelta(hours=reminder_hours()),
        created_at__gt=now - timedelta(hours=hold_hours() - 1),
    ).exclude(email="").order_by("created_at")


def release(order):
    """Cancel an unpaid online order without notifying anyone; returns False if it was paid or changed meanwhile."""
    with transaction.atomic():
        locked = _unpaid_online().select_for_update().filter(pk=order.pk).first()
        if locked is None:
            return False
        locked._quiet_cancel = True  # orders.signals: return the stock, but send no emails or pushes
        locked.order_status = Order.OrderStatus.CANCELLED
        locked.payment_status = Order.PaymentStatus.FAILED
        locked.save(update_fields=["order_status", "payment_status", "updated_at"])
    logger.info("Released unpaid order %s", locked.formatted_id)
    return True


def retake_stock_if_cancelled(order):
    """A payment arrived for an order that was already cancelled (and its stock returned): take the stock again.

    Rare: the customer started paying just before the order was released. Stock may go below zero, which
    shows staff the order needs attention rather than silently overselling.
    """
    if order.order_status != Order.OrderStatus.CANCELLED:
        return
    for item in order.items.all():
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") - item.quantity)
    logger.warning("Order %s was paid after it had been cancelled; its stock was taken again", order.formatted_id)
