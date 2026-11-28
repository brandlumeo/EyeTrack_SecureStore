"""Make the storefront WebP copies (store.images) when a photo is saved."""
from django.apps import apps
from django.db.models.signals import post_save

from . import images

# model label -> image fields shown on the storefront
IMAGE_FIELDS = {
    "store.Product": ("image",),
    "store.ProductGallery": ("image",),
    "store.Project": ("cover_image",),
    "store.ProjectImage": ("image",),
    "orders.InstallationPhoto": ("image",),  # homepage "Recent installations"
    "orders.Technician": ("photo",),  # order tracking
    "support.ViewingGuide": ("image",),
    "store.ReviewMedia": ("file",),  # review photos (videos are skipped)
}


def thumb_targets():
    """(model class, field names) pairs, for the make_thumbnails command."""
    return [(apps.get_model(label), fields) for label, fields in IMAGE_FIELDS.items()]


def _make(sender, instance, raw=False, **kwargs):
    if raw:  # loaddata
        return
    for field in IMAGE_FIELDS[sender._meta.label]:
        images.make_thumbs(getattr(instance, field))


for _label in IMAGE_FIELDS:
    post_save.connect(_make, sender=_label, dispatch_uid="store_thumbs_" + _label)


# ---- Store every uploaded photo as WebP ----
from django.db import models as _models  # noqa: E402
from django.db.models.signals import pre_save  # noqa: E402

# FileFields (not ImageFields) that also take photos; videos are left alone.
EXTRA_PHOTO_FIELDS = {"store.ReviewMedia": ("file",)}


def webp_targets():
    """(model class, field names) for every field that stores photos."""
    out = []
    for model in apps.get_models():
        fields = [f.name for f in model._meta.concrete_fields if isinstance(f, _models.ImageField)]
        fields += [n for n in EXTRA_PHOTO_FIELDS.get(model._meta.label, ()) if n not in fields]
        if fields:
            out.append((model, tuple(fields)))
    return out


def _to_webp(sender, instance, raw=False, **kwargs):
    if raw:
        return
    for field in _WEBP_FIELDS[sender]:
        converted = images.webp_upload(getattr(instance, field))
        if converted is not None:
            setattr(instance, field, converted)  # saved via upload_to as <stem>.webp


_WEBP_FIELDS = dict(webp_targets())
for _model in _WEBP_FIELDS:
    pre_save.connect(_to_webp, sender=_model, dispatch_uid="store_webp_" + _model._meta.label)
