"""Where we deliver and install.

Delivery: any valid Indian pincode. Installation: Kerala pincodes in INSTALLATION_DISTRICTS.
A pincode's district comes from India Post's public lookup and is saved in PincodeLookup, so each
pincode is looked up once. Rows in ServiceableArea (admin dashboard) override the defaults for a pincode.
"""
import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from decimal import Decimal

from .models import PincodeLookup, ServiceableArea

logger = logging.getLogger(__name__)

INSTALLATION_DISTRICTS = {"Kozhikode", "Kannur", "Malappuram"}
HOME_DISTRICTS = {"Kozhikode"}
HOME_DELIVERY_DAYS = 5
DELIVERY_DAYS = 7
# Free delivery for now; the business will set a fee later. Orders of FREE_SHIPPING_FROM or more always ship free.
DEFAULT_DELIVERY_CHARGE = Decimal("0.00")
FREE_SHIPPING_FROM = Decimal("5000.00")

LOOKUP_URL = "https://api.postalpincode.in/pincode/%s"
LOOKUP_TIMEOUT = 4
PINCODE_RE = re.compile(r"^[1-8]\d{5}$")


@dataclass
class Serviceability:
    pincode: str
    valid: bool
    delivery_available: bool = False
    installation_available: bool = False
    installation_unverified: bool = False  # the district lookup failed, so installation couldn't be confirmed
    estimated_days: int = DELIVERY_DAYS
    delivery_charge: Decimal = DEFAULT_DELIVERY_CHARGE
    district: str = ""
    state: str = ""


def is_valid_pincode(pincode):
    return bool(PINCODE_RE.match(pincode or ""))


def _fetch(pincode):
    """(district, state) from India Post, or None when the pincode is unknown or the service is unreachable."""
    try:
        with urllib.request.urlopen(LOOKUP_URL % pincode, timeout=LOOKUP_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        ok = bool(data) and data[0].get("Status") == "Success"
        offices = (data[0].get("PostOffice") or []) if ok else []
    except Exception:
        logger.warning("Pincode lookup failed for %s", pincode, exc_info=True)
        return None
    if not offices:
        return None
    return offices[0].get("District", "").strip(), offices[0].get("State", "").strip()


def lookup_district(pincode):
    """(district, state) for a pincode, from the saved lookups or India Post; None if it can't be determined."""
    saved = PincodeLookup.objects.filter(pincode=pincode).first()
    if saved:
        return saved.district, saved.state
    found = _fetch(pincode)
    if found and all(found):
        PincodeLookup.objects.update_or_create(pincode=pincode, defaults={"district": found[0], "state": found[1]})
        return found
    return None


def check(pincode):
    """Delivery and installation for a pincode, applying any admin override."""
    pincode = (pincode or "").strip()
    result = Serviceability(pincode=pincode, valid=is_valid_pincode(pincode))
    if not result.valid:
        return result

    override = ServiceableArea.objects.filter(pincode=pincode).first()
    if override:
        # Staff set this pincode by hand: no lookup needed (use a saved district if we have one, for display).
        saved = PincodeLookup.objects.filter(pincode=pincode).first()
        if saved:
            result.district, result.state = saved.district, saved.state
        result.delivery_available = override.delivery_available
        result.installation_available = override.delivery_available and override.installation_available
        result.estimated_days = override.estimated_delivery_days
        result.delivery_charge = override.delivery_charge
        return result

    found = lookup_district(pincode)
    if found:
        result.district, result.state = found
    result.delivery_available = True
    if found:
        result.installation_available = result.state.lower() == "kerala" and result.district in INSTALLATION_DISTRICTS
        result.estimated_days = HOME_DELIVERY_DAYS if result.district in HOME_DISTRICTS else DELIVERY_DAYS
    else:
        result.installation_unverified = True
    return result


def delivery_charge(pincode, subtotal):
    """Shipping for an order of `subtotal` to `pincode` (no lookup needed: only overrides change the default)."""
    if subtotal >= FREE_SHIPPING_FROM:
        return Decimal("0.00")
    override = ServiceableArea.objects.filter(pincode=(pincode or "").strip()).first() if pincode else None
    return override.delivery_charge if override else DEFAULT_DELIVERY_CHARGE


def installation_districts_label():
    return ", ".join(sorted(INSTALLATION_DISTRICTS))
