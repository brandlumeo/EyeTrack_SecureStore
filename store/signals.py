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
