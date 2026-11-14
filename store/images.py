"""Resized WebP copies of uploaded photos, for the storefront.

Uploads stay untouched (they are still used for Open Graph, JSON-LD, the
Razorpay checkout and staff screens). Visitors get light WebP copies at a
few fixed widths, stored next to the media as ``thumbs/<width>/<name>.webp``.

Copies are made when a photo is saved (see ``store.signals``) and by the
``make_thumbnails`` command for photos that already exist. Pages never make
them while rendering: a missing copy falls back to the original upload, so
a page is never slowed down or broken by this.
"""
import logging
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

WIDTHS = (400, 800, 1200)
QUALITY = 80
THUMB_DIR = "thumbs"


def thumb_name(name, width):
    return "%s/%d/%s.webp" % (THUMB_DIR, width, os.path.splitext(name)[0])


def _widths_for(source_width):
    """The smallest width always; larger ones only if the photo is big enough
    for them (no upscaling a 500px photo into a blurry '1200w' copy)."""
    out = [WIDTHS[0]]
    for w in WIDTHS[1:]:
        if source_width >= w * 0.9:
            out.append(w)
    return out


def make_thumbs(field_file, force=False):
    """Write the WebP copies for one ImageField value. Returns the widths made
    (or already present). Never raises: a bad file just gets no copies."""
    if not field_file or not field_file.name:
        return []
    storage = field_file.storage
    if not force and storage.exists(thumb_name(field_file.name, WIDTHS[0])):
        return sorted(available(field_file))  # already done; skip decoding the photo
    try:
        with storage.open(field_file.name, "rb") as fh:
            img = Image.open(fh)
            img.load()
    except UnidentifiedImageError:  # e.g. AVIF, which this Pillow can't read
        logger.warning("Unsupported image format, no thumbnails: %s", field_file.name)
        return []
    except FileNotFoundError:
        logger.warning("Image file missing, no thumbnails: %s", field_file.name)
        return []
    except Exception:
        logger.warning("Could not open image %s for thumbnails", field_file.name, exc_info=True)
        return []

    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() or img.mode == "P" else "RGB")

    made = []
    for width in _widths_for(img.width):
        dst = thumb_name(field_file.name, width)
        if storage.exists(dst):
            if not force:
                made.append(width)
                continue
            storage.delete(dst)
        copy = img.copy()
        if copy.width > width:
            copy.thumbnail((width, width * 10), Image.LANCZOS)
        buf = BytesIO()
        try:
            copy.save(buf, "WEBP", quality=QUALITY, method=4)
            storage.save(dst, ContentFile(buf.getvalue()))
        except Exception:
            logger.warning("Could not write thumbnail %s", dst, exc_info=True)
            continue
        made.append(width)
    return made


def available(field_file):
    """{width: url} for the copies that exist for this ImageField value."""
    if not field_file or not field_file.name:
        return {}
    storage = field_file.storage
    found = {}
    for width in WIDTHS:
        dst = thumb_name(field_file.name, width)
        try:
            if storage.exists(dst):
                found[width] = storage.url(dst)
        except Exception:
            pass
    return found


def thumb_url(field_file, width):
    """URL of the copy closest to ``width`` (the next larger one if possible),
    else the original upload."""
    if not field_file or not field_file.name:
        return ""
    found = available(field_file)
    if found:
        larger = [w for w in found if w >= width]
        return found[min(larger)] if larger else found[max(found)]
    try:
        return field_file.url
    except Exception:
        return ""
