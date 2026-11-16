"""Prices in Indian format: {{ product.price|inr }} -> 7,200 / 1,25,000 (no decimals unless there are paise)."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def inr(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value
    negative = amount < 0
    amount = abs(amount)
    rupees = int(amount)
    paise = int((amount - rupees) * 100 + Decimal("0.5"))
    if paise == 100:
        rupees, paise = rupees + 1, 0
    digits = str(rupees)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    out = digits + (".%02d" % paise if paise else "")
    return "-" + out if negative else out
