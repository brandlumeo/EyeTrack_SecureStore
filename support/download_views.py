"""Public download centre: manuals, datasheets, brochures and software links managed by staff."""
import os

from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .models import Download

INLINE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def download_list(request):
    downloads = Download.objects.filter(is_published=True)
    brands = sorted({d.brand for d in downloads if d.brand})
    kinds = [(value, label) for value, label in Download.Kind.choices if any(d.kind == value for d in downloads)]

    kind = request.GET.get("type", "")
    brand = request.GET.get("brand", "")
    query = request.GET.get("q", "").strip()[:80]
    if kind not in dict(kinds):
        kind = ""
    if brand not in brands:
        brand = ""
    if kind:
        downloads = downloads.filter(kind=kind)
    if brand:
        downloads = downloads.filter(brand=brand)
    if query:
        downloads = downloads.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(brand__icontains=query))

    return render(request, "support/downloads/list.html", {
        "downloads": downloads,
        "kinds": kinds,
        "brands": brands,
        "active_kind": kind,
        "active_brand": brand,
        "query": query,
        "is_filtered": bool(kind or brand or query),
    })


def download_file(request, pk):
    item = get_object_or_404(Download, pk=pk)
    if not item.is_published and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404("Download not found")
    if item.is_published:
        Download.objects.filter(pk=item.pk).update(download_count=F("download_count") + 1)
    if item.is_external:
        return redirect(item.external_url)
    if not item.file:
        raise Http404("Download not found")
    ext = os.path.splitext(item.file.name)[1].lower()
    try:
        handle = item.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("File missing")
    return FileResponse(handle, as_attachment=ext not in INLINE_EXTENSIONS,
                        filename="%s%s" % (slugify(item.title) or "download", ext))
