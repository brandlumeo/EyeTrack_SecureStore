"""Local area pages: one per district where we install, plus a hub listing them."""
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import render

from . import serviceability
from .areas import AREAS, INSTALL_CATEGORY_SLUGS
from .models import Category, Project


def _categories():
    counts = Category.objects.filter(slug__in=INSTALL_CATEGORY_SLUGS).annotate(
        product_count=Count("products", filter=Q(products__is_available=True)))
    by_slug = {c.slug: c for c in counts if c.product_count}
    return [by_slug[s] for s in INSTALL_CATEGORY_SLUGS if s in by_slug]


def area_list(request):
    return render(request, "store/areas/list.html", {
        "areas": [dict(area, slug=slug) for slug, area in AREAS.items()],
        "delivery_days": serviceability.DELIVERY_DAYS,
    })


def area_detail(request, district):
    area = AREAS.get(district)
    if area is None:
        raise Http404("We don't have a page for this area")
    places = [area["name"]] + area["towns"]
    match = Q()
    for place in places:
        match |= Q(location__icontains=place.replace(" city", "").replace(" town", ""))
    projects = Project.objects.filter(match, is_published=True).order_by("-completed_on", "-id")[:3]
    home = area["name"] in serviceability.HOME_DISTRICTS
    return render(request, "store/areas/detail.html", {
        "area": dict(area, slug=district),
        "categories": _categories(),
        "projects": projects,
        "delivery_days": serviceability.HOME_DELIVERY_DAYS if home else serviceability.DELIVERY_DAYS,
        "other_areas": [dict(a, slug=s) for s, a in AREAS.items() if s != district],
    })
