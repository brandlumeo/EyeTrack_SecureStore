"""Public projects gallery (completed installations managed from the admin dashboard)."""
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Project


def project_list(request):
    site_type = request.GET.get("type", "")
    projects = Project.objects.filter(is_published=True)
    valid_types = dict(Project.SiteType.choices)
    if site_type in valid_types:
        projects = projects.filter(site_type=site_type)
    else:
        site_type = ""
    # Only offer filters for property types that actually have published projects.
    used = set(Project.objects.filter(is_published=True).values_list("site_type", flat=True))
    filters = [(value, label) for value, label in Project.SiteType.choices if value in used]
    page_obj = Paginator(projects.order_by("-is_featured", "order", "-completed_on", "-created_at"), 12).get_page(request.GET.get("page"))
    return render(request, "store/projects/list.html", {
        "projects": page_obj,
        "page_obj": page_obj,
        "filters": filters,
        "active_type": site_type,
        "has_projects": bool(used),
    })


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.prefetch_related("images", "products"), slug=slug)
    is_preview = not project.is_published
    if is_preview and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404("Project not found")
    related = (Project.objects.filter(is_published=True, site_type=project.site_type)
               .exclude(pk=project.pk).order_by("order", "-completed_on")[:3])
    return render(request, "store/projects/detail.html", {
        "project": project,
        "is_preview": is_preview,
        "related": related,
        "products": [p for p in project.products.all() if p.is_available],
    })
