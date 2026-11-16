"""Links to the local area pages (/cctv-installation/<district>/) from the rest of the site.

    {% load area_tags %}
    {% areas_served %}                       full "Areas we serve" block (homepage)
    {% areas_served category=category %}     same, only for categories we install
    {% areas_inline %}                       "Kozhikode, Kannur and Malappuram" as links
    {% area_for project.location as area %}  the district page matching a place name
"""
from django import template
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from store.areas import AREAS, INSTALL_CATEGORY_SLUGS

register = template.Library()

TOWNS_SHOWN = 6


def _areas():
    out = []
    for slug, area in AREAS.items():
        out.append({
            "slug": slug,
            "name": area["name"],
            "url": reverse("area_detail", args=[slug]),
            "towns": area["towns"][:TOWNS_SHOWN],
            "more": max(len(area["towns"]) - TOWNS_SHOWN, 0),
        })
    return out


@register.inclusion_tag("store/includes/areas_served.html")
def areas_served(category=None):
    show = category is None or getattr(category, "slug", None) in INSTALL_CATEGORY_SLUGS
    return {
        "show": show,
        "areas": _areas() if show else [],
        "area_list_url": reverse("area_list"),
        "category": category,
    }


@register.simple_tag
def areas_inline():
    areas = _areas()
    links = format_html_join(", ", '<a href="{}">{}</a>', ((a["url"], a["name"]) for a in areas[:-1]))
    last = areas[-1]
    if len(areas) == 1:
        return format_html('<a href="{}">{}</a>', last["url"], last["name"])
    return format_html('{} and <a href="{}">{}</a>', links, last["url"], last["name"])


def _clean(place):
    return place.replace(" city", "").replace(" town", "").strip().lower()


@register.simple_tag
def area_for(location):
    """The area page for a free-text location such as "Perambra, Kozhikode", or None."""
    text = (location or "").lower()
    if not text:
        return None
    for area in _areas():
        names = [area["name"]] + AREAS[area["slug"]]["towns"]
        if any(_clean(n) and _clean(n) in text for n in names):
            return area
    return None
