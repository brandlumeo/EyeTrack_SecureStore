"""Public remote-viewing guides (content managed by staff in the admin dashboard)."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import ViewingGuide


def guide_list(request):
    guides = ViewingGuide.objects.filter(is_published=True)
    brands = sorted({g.brand for g in guides if g.brand.lower() != "general"})
    brand = request.GET.get("brand", "")
    if brand in brands:
        guides = [g for g in guides if g.brand == brand or g.brand.lower() == "general"]
    else:
        brand = ""
    return render(request, "support/guides/list.html", {"guides": guides, "brands": brands, "active_brand": brand})


def guide_detail(request, slug):
    guide = get_object_or_404(ViewingGuide, slug=slug)
    is_preview = not guide.is_published
    if is_preview and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404("Guide not found")
    others = ViewingGuide.objects.filter(is_published=True).exclude(pk=guide.pk)[:4]
    return render(request, "support/guides/detail.html", {"guide": guide, "is_preview": is_preview, "others": others})
