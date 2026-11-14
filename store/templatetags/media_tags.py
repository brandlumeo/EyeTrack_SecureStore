"""Light WebP photos for the storefront (see store.images).

    {% load media_tags %}
    <img src="{{ product.image|thumb:400 }}" {% srcset product.image %} sizes="..." alt="...">

Both fall back to the original upload when no WebP copy exists yet.
"""
from django import template
from django.utils.html import format_html

from store import images

register = template.Library()


@register.filter
def thumb(field_file, width=800):
    return images.thumb_url(field_file, int(width))


@register.simple_tag
def srcset(field_file):
    """srcset="…400w, …800w" for the copies that exist, or nothing."""
    found = images.available(field_file)
    if len(found) < 2:
        return ""
    return format_html('srcset="{}"', ", ".join("%s %dw" % (url, w) for w, url in sorted(found.items())))
