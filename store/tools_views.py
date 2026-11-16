"""CCTV planning tools: system builder, storage and lens calculators, camera guide."""
from urllib.parse import urlencode

from django import forms
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from support.models import QuoteRequest

from .models import Product
from .tools import (
    BITRATE_MBPS,
    HDD_HEADROOM,
    HDD_SIZES_TB,
    RESOLUTION_LABELS,
    RESOLUTIONS,
    SENSOR_WIDTH_MM,
    CameraGroup,
    lens_estimate,
    recommend_system,
    storage_estimate,
)

RESOLUTION_CHOICES = [(r, RESOLUTION_LABELS[r]) for r in RESOLUTIONS]
DAY_CHOICES = [(7, "7 days"), (15, "15 days"), (30, "30 days"), (60, "60 days"), (90, "90 days")]


class StorageForm(forms.Form):
    cameras = forms.IntegerField(min_value=1, max_value=128, initial=4)
    resolution = forms.ChoiceField(choices=RESOLUTION_CHOICES, initial="4MP")
    days = forms.TypedChoiceField(choices=DAY_CHOICES, coerce=int, initial=30)
    codec = forms.ChoiceField(choices=[("h265", "H.265 (recommended)"), ("h264", "H.264")], initial="h265")
    fps = forms.TypedChoiceField(choices=[(10, "10 fps"), (15, "15 fps"), (20, "20 fps"), (25, "25 fps")], coerce=int, initial=25)
    hours = forms.IntegerField(min_value=1, max_value=24, initial=24)
    mode = forms.ChoiceField(choices=[("continuous", "Continuous"), ("motion", "Motion only")], initial="continuous")
    activity = forms.IntegerField(min_value=5, max_value=100, initial=30)

    def estimate(self):
        d = self.cleaned_data
        activity = d["activity"] if d["mode"] == "motion" else 100
        return storage_estimate([CameraGroup(d["cameras"], d["resolution"])], days=d["days"], codec=d["codec"],
                                fps=d["fps"], hours_per_day=d["hours"], activity_pct=activity)


class LensForm(forms.Form):
    distance = forms.FloatField(min_value=1, max_value=200, initial=10, label="Distance to target (m)")
    width = forms.FloatField(min_value=0.5, max_value=200, initial=6, label="Width to cover (m)")
    sensor = forms.ChoiceField(choices=[(s, s) for s in SENSOR_WIDTH_MM], initial='1/2.8"')
    resolution = forms.ChoiceField(choices=RESOLUTION_CHOICES, initial="4MP")

    def estimate(self):
        d = self.cleaned_data
        return lens_estimate(d["distance"], d["width"], d["sensor"], d["resolution"])


class BuilderForm(forms.Form):
    site_type = forms.ChoiceField(choices=QuoteRequest.SiteType.choices, initial="home")
    outdoor = forms.IntegerField(min_value=0, max_value=64, initial=2)
    indoor = forms.IntegerField(min_value=0, max_value=64, initial=2)
    night = forms.ChoiceField(choices=[("ir", "Standard infrared (black & white)"), ("colour", "Full-colour night vision")], initial="ir")
    audio = forms.ChoiceField(choices=[("no", "No"), ("yes", "Yes")], initial="no")
    days = forms.TypedChoiceField(choices=DAY_CHOICES[:3], coerce=int, initial=30)
    cabling = forms.ChoiceField(
        choices=[("yes", "Yes, cables are fine"), ("unsure", "Not sure"), ("wireless", "Prefer wireless")], initial="yes")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("outdoor", 0) + cleaned.get("indoor", 0) == 0:
            raise forms.ValidationError("Add at least one camera point, indoor or outdoor.")
        return cleaned


# Icons and one-line descriptions for the system builder's answer cards.
BUILDER_OPTION_DETAILS = {
    "site_type": {
        "home": ("bi-house-door", "Independent house or villa"),
        "apartment": ("bi-buildings", "Flat or apartment block"),
        "shop": ("bi-shop", "Showroom, store or outlet"),
        "office": ("bi-briefcase", "Workspace or reception"),
        "factory": ("bi-boxes", "Yard, loading bay, storage"),
        "school": ("bi-mortarboard", "Campus, gates, classrooms"),
        "hospital": ("bi-hospital", "Wards, entrances, pharmacy"),
        "other": ("bi-three-dots", "Something else"),
    },
    "night": {
        "ir": ("bi-moon-stars", "Clear black-and-white video in the dark. Works with no light at all."),
        "colour": ("bi-palette", "Shows clothing and vehicle colours at night. Needs a little ambient light."),
    },
    "audio": {
        "no": ("bi-mic-mute", "Video only"),
        "yes": ("bi-mic", "Hear what happens on camera"),
    },
    "days": {
        7: ("bi-calendar-week", "Smallest hard disk"),
        15: ("bi-calendar2-range", "A good balance"),
        30: ("bi-calendar3", "Most popular"),
    },
    "cabling": {
        "yes": ("bi-ethernet", "Most reliable picture and recording"),
        "unsure": ("bi-question-circle", "We'll check on the site survey"),
        "wireless": ("bi-wifi", "For finished interiors where wiring is hard"),
    },
}


def _builder_options(form):
    options = {}
    for name, details in BUILDER_OPTION_DETAILS.items():
        options[name] = [
            {"value": value, "label": label, "icon": details.get(value, ("bi-circle", ""))[0],
             "description": details.get(value, ("", ""))[1]}
            for value, label in form.fields[name].choices
        ]
    return options


def _initial_data(form_class):
    return {name: field.initial for name, field in form_class.base_fields.items()}


def _bound(form_class, request):
    """Bind GET data when present, falling back to each field's initial value for missing keys."""
    if not request.GET:
        return form_class(), False
    data = {name: request.GET.get(name, field.initial) for name, field in form_class.base_fields.items()}
    return form_class(data), True


def _calculator(request, form_class, template, extra=None):
    """Render a calculator; with no query yet, show the result for the default inputs."""
    form, submitted = _bound(form_class, request)
    calc = form if submitted else form_class(_initial_data(form_class))
    result = calc.estimate() if calc.is_valid() else None
    return render(request, template, {"form": form, "result": result, **(extra or {})})


REFERENCE_DAYS = [7, 15, 30, 60, 90]


def _storage_reference(cameras=4):
    """Recommended drive for `cameras` cameras (H.265, 25 fps, 24 h) by resolution and retention."""
    rows = []
    for resolution in RESOLUTIONS:
        cells = []
        for days in REFERENCE_DAYS:
            hdd = storage_estimate([CameraGroup(cameras, resolution)], days=days)["hdd"]
            cells.append(f"{hdd['drives']} × {hdd['size_tb']} TB" if hdd["drives"] > 1 else f"{hdd['size_tb']} TB")
        rows.append({"resolution": RESOLUTION_LABELS[resolution], "cells": cells})
    return {"cameras": cameras, "days": REFERENCE_DAYS, "rows": rows}


def tools_hub(request):
    return render(request, "store/tools/hub.html")


def camera_guide(request):
    return render(request, "store/tools/camera_guide.html")


def storage_calculator(request):
    return _calculator(request, StorageForm, "store/tools/storage_calculator.html", extra={
        "reference": _storage_reference(),
        # Same constants the server uses, so the page can show the estimate instantly while the API confirms it.
        "storage_config": {"bitrates": BITRATE_MBPS, "hdd_sizes": HDD_SIZES_TB, "headroom": HDD_HEADROOM},
    })


def lens_calculator(request):
    return _calculator(request, LensForm, "store/tools/lens_calculator.html")


def _calculator_api(request, form_class):
    form = form_class({**_initial_data(form_class), **request.GET.dict()})
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, "result": form.estimate()})


def storage_api(request):
    return _calculator_api(request, StorageForm)


def lens_api(request):
    return _calculator_api(request, LensForm)


def system_builder(request):
    if "outdoor" in request.GET or "indoor" in request.GET:
        form, submitted = _bound(BuilderForm, request)
    else:
        # e.g. ?site_type=shop from a project page: preselect the answer, don't jump to a plan
        site_type = request.GET.get("site_type")
        form = BuilderForm(initial={"site_type": site_type} if site_type in dict(QuoteRequest.SiteType.choices) else None)
        submitted = False
    plan = products = quote_url = None
    if submitted and form.is_valid():
        d = form.cleaned_data
        plan = recommend_system(d["site_type"], d["outdoor"], d["indoor"], night=d["night"],
                                audio=d["audio"] == "yes", days=d["days"], cabling=d["cabling"])
        products = list(
            Product.objects.filter(is_available=True, camera_type__in=plan["camera_types"]).order_by("-stock", "-created_at")[:4]
        ) or list(
            Product.objects.filter(is_available=True, category__slug="cctv-installation").order_by("-stock", "-created_at")[:4]
        )
        quote_url = reverse("quote_request") + "?" + urlencode({
            "site_type": d["site_type"],
            "camera_count": plan["quote_camera_count"],
            "package": plan["package"],
            "message": "System builder plan: " + plan["summary"],
        })
    return render(request, "store/tools/system_builder.html", {
        "form": form, "submitted": submitted, "plan": plan, "products": products, "quote_url": quote_url,
        "options": _builder_options(form),
    })
