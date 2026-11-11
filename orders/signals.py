import logging
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Invoice, Order, OrderItem, Payment
from config.firebase_setup import initialize_firebase, is_firebase_ready

try:
    import firebase_admin
    from firebase_admin import messaging
except ModuleNotFoundError:
    firebase_admin = None
    messaging = None

logger = logging.getLogger(__name__)


from .emails import (
    send_admin_order_notification_email, 
    send_order_status_update_email,
    send_email_async
)

def _schedule_invoice_sync(order_id):
    if not order_id:
        return
    # Run synchronously on commit for reliability in shared hosting
    transaction.on_commit(lambda: Invoice.sync_for_order_id(order_id))


@receiver(post_save, sender=Order)
def sync_invoice_from_order(sender, instance, **kwargs):
    _schedule_invoice_sync(instance.pk)


@receiver(post_save, sender=OrderItem)
def sync_invoice_from_order_item_save(sender, instance, **kwargs):
    _schedule_invoice_sync(instance.order_id)


@receiver(post_delete, sender=OrderItem)
def sync_invoice_from_order_item_delete(sender, instance, **kwargs):
    _schedule_invoice_sync(instance.order_id)


@receiver(post_save, sender=Payment)
def sync_invoice_from_payment(sender, instance, **kwargs):
    _schedule_invoice_sync(instance.order_id)


# Statuses that should trigger a customer-facing status update email
STATUS_EMAIL_TRANSITIONS = {
    Order.OrderStatus.CONFIRMED,
    Order.OrderStatus.PROCESSING,
    Order.OrderStatus.SHIPPED,
    Order.OrderStatus.DELIVERED,
    Order.OrderStatus.CANCELLED,
}

@receiver(post_save, sender=Order)
def notify_admin_on_order_update(sender, instance, created, **kwargs):
    if created:
        # New order placed — admin notification.
        # For Online orders, we wait until payment success in views.py
        if instance.payment_method == Order.PaymentMethod.COD:
            transaction.on_commit(
                lambda: send_email_async(send_admin_order_notification_email, instance.id, event_type="placed")
            )
    else:
        original_status = getattr(instance, "_original_order_status", None)
        current_status = instance.order_status
        # orders.stock.release: an abandoned online payment, cancelled without emails or pushes.
        quiet = getattr(instance, "_quiet_cancel", False)

        # Status genuinely changed?
        if original_status is not None and original_status != current_status:
            # Admin cancellation notification
            if (original_status != Order.OrderStatus.CANCELLED and
                    current_status == Order.OrderStatus.CANCELLED):
                if not quiet:
                    transaction.on_commit(
                        lambda: send_email_async(send_admin_order_notification_email, instance.id, event_type="cancelled")
                    )
                
                # Restock items automatically on cancellation
                _restock_order_items(instance)

            # Customer-facing status update email for tracked transitions
            if current_status in STATUS_EMAIL_TRANSITIONS and not quiet:
                # Capture values in closure to avoid stale instance references
                order_id = instance.id
                new_status = current_status
                transaction.on_commit(
                    lambda oid=order_id, ns=new_status: send_email_async(send_order_status_update_email, oid, ns)
                )

                # Send Firebase Push Notification synchronously on commit (fast enough)
                transaction.on_commit(
                    lambda oid=order_id, ns=new_status: _send_fcm_notification(oid, ns)
                )
                
                # Send In-App DB Notification
                transaction.on_commit(
                    lambda oid=order_id, ns=new_status: _create_db_notification(oid, ns)
                )

    # Track shipping status changes (Out for Delivery)
    original_shipping = getattr(instance, "_original_shipping_status", None)
    current_shipping = instance.shipping_status

    if original_shipping is not None and original_shipping != current_shipping:
        if current_shipping == Order.ShippingStatus.OUT_FOR_DELIVERY:
            order_id = instance.id
            transaction.on_commit(
                lambda oid=order_id: send_email_async(send_order_status_update_email, oid, "out_for_delivery")
            )
            transaction.on_commit(
                lambda oid=order_id: _send_fcm_notification(oid, "out_for_delivery")
            )
            transaction.on_commit(
                lambda oid=order_id: _create_db_notification(oid, "out_for_delivery")
            )

    # Track current status for next save within this instance's lifecycle
    instance._original_order_status = instance.order_status
    instance._original_shipping_status = instance.shipping_status


def _create_db_notification(order_id, current_status):
    try:
        from orders.models import Order
        from accounts.models import Notification
        order = Order.objects.get(id=order_id)
        if not order.user:
            return
            
        title = "Order Update"
        if current_status == "out_for_delivery":
            message = f"Good news! Your order {order.formatted_id} is out for delivery."
        elif current_status == Order.OrderStatus.DELIVERED:
            title = "Order Delivered"
            message = f"Your order {order.formatted_id} has been delivered successfully. Thank you for shopping with us!"
        elif current_status == Order.OrderStatus.SHIPPED:
            message = f"Your order {order.formatted_id} has been shipped and is on its way."
        elif current_status == Order.OrderStatus.PROCESSING:
            message = f"Your order {order.formatted_id} is now being processed."
        elif current_status == Order.OrderStatus.CONFIRMED:
            return  # Skip confirmed as the checkout view manually handles the 'Payment Confirmed' notification
        elif current_status == Order.OrderStatus.CANCELLED:
            title = "Order Cancelled"
            message = f"Your order {order.formatted_id} has been cancelled."
        else:
            message = f"Your order {order.formatted_id} status has been updated to: {order.get_order_status_display()}."

        Notification.send(
            user=order.user,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.ORDER,
            link=f"/accounts/orders/{order.id}/track/"
        )
    except Exception as e:
        logger.error(f"Failed to create DB notification for order {order_id}: {str(e)}")

def _send_fcm_notification(order_id, current_status):
    if messaging is None:
        logger.info("firebase_admin is not installed. Skipping FCM notification for order %s.", order_id)
        return
    if not is_firebase_ready() and not initialize_firebase():
        logger.warning("Firebase Admin SDK is not ready. Skipping FCM notification for order %s.", order_id)
        return

    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        if order.user and hasattr(order.user, 'profile') and order.user.profile.fcm_token:
            profile = order.user.profile
            token = profile.fcm_token
            status_display = order.get_order_status_display()
            msg = messaging.Message(
                notification=messaging.Notification(
                    title='Eyetrack Update',
                    body=f'Your order {order.formatted_id} is now {status_display}.'
                ),
                token=token,
            )
            try:
                messaging.send(msg)
            except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
                # Google says this token will never work again (app/browser unregistered, or it belongs to
                # another Firebase project). Forget it instead of retrying it on every order update.
                type(profile).objects.filter(pk=profile.pk, fcm_token=token).update(fcm_token=None)
                logger.info("Cleared stale FCM token for user %s after order %s update.", order.user_id, order_id)
    except Exception as e:
        logger.error(f"Failed to send FCM notification for order {order_id}: {str(e)}")

def _restock_order_items(order):
    """Returns reserved stock to products when an order is cancelled."""
    try:
        with transaction.atomic():
            for item in order.items.select_related('product').all():
                product = item.product
                product.stock += item.quantity
                product.save(update_fields=['stock'])
                logger.info(f"Restocked {item.quantity} units of {product.name} for cancelled order {order.formatted_id}")
    except Exception as e:
        logger.error(f"Failed to restock items for order {order.formatted_id}: {str(e)}")
