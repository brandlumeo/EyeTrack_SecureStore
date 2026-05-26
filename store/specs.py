SPEC_TYPE_CCTV = "cctv"
SPEC_TYPE_VIDEO_DOOR_PHONE = "video_door_phone"
SPEC_TYPE_BIOMETRIC = "biometric"
SPEC_TYPE_SMART_LOCK = "smart_lock"
SPEC_TYPE_NETWORK = "network"


def get_product_spec_type(product_or_category):
    """Resolve a product/category to the shared spec group used across admin and storefront."""
    category = getattr(product_or_category, "category", product_or_category)
    if not category:
        return None

    name = (getattr(category, "name", "") or "").strip().lower()
    slug = (getattr(category, "slug", "") or "").strip().lower()

    if name == "video door phones":
        return SPEC_TYPE_VIDEO_DOOR_PHONE
    if name in {"cctv cameras", "cctv installation"}:
        return SPEC_TYPE_CCTV
    if name == "biometric devices":
        return SPEC_TYPE_BIOMETRIC
    if name == "smart locks":
        return SPEC_TYPE_SMART_LOCK
    if name in {"network cabling", "it consulting"}:
        return SPEC_TYPE_NETWORK

    if slug in {"homegate-automation", "video-door-phones"} or ("video" in slug and "door" in slug):
        return SPEC_TYPE_VIDEO_DOOR_PHONE
    if "cctv" in slug or "camera" in slug:
        return SPEC_TYPE_CCTV
    if "biometric" in slug:
        return SPEC_TYPE_BIOMETRIC
    if "smart-lock" in slug or "lock" in slug:
        return SPEC_TYPE_SMART_LOCK
    if any(token in slug for token in ("network", "switch", "router", "consulting")):
        return SPEC_TYPE_NETWORK

    return None
