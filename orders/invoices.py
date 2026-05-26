from orders.models import Invoice


def format_customer_name(value):
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


def format_address(value):
    segments = []
    for line in str(value or "").splitlines():
        for segment in line.split(","):
            cleaned = " ".join(segment.split())
            if cleaned:
                segments.append(cleaned)
    return ", ".join(segments) or "Address not available"


def get_payment_method_label(payment):
    if payment:
        return payment.get_payment_method_display()
    return "Pending confirmation"


def build_invoice_bundle(order):
    invoice = Invoice.sync_for_order(order)
    latest_payment = order.payments.order_by("-created_at", "-id").first()
    items = list(order.items.select_related("product").all())
    total_units = 0
    for index, item in enumerate(items, start=1):
        item.line_total = item.price * item.quantity
        item.sequence = index
        total_units += item.quantity

    invoice_display = {
        "invoice_number": invoice.invoice_number,
        "recipient_name": format_customer_name(order.full_name),
        "address": format_address(order.address),
        "payment_status": invoice.get_payment_status_display(),
        "payment_method": get_payment_method_label(latest_payment),
        "transaction_id": latest_payment.transaction_id if latest_payment and latest_payment.transaction_id else f"ET-ORD-{order.id:06d}",
        "issued_date": invoice.created_at,
        "order_date": order.created_at,
        "order_reference": f"ET-{order.id:06d}",
        "subtotal": invoice.subtotal,
        "tax": invoice.tax,
        "shipping_cost": invoice.shipping_cost,
        "total_amount": invoice.total_amount,
        "item_count": len(items),
        "unit_count": total_units,
        "support_email": "info@etsgrp.in",
        "support_phone": "+91 7994357565",
    }
    return {
        "invoice": invoice,
        "latest_payment": latest_payment,
        "invoice_items": items,
        "invoice_display": invoice_display,
    }
