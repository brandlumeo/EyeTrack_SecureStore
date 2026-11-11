"""Starter remote-viewing guides, created as UNPUBLISHED drafts.

Menu names differ between recorder models, firmware and app versions, so staff must check each guide
against a real recorder and the current app before publishing it from the admin dashboard.
App store links are left blank on purpose: paste the exact links from Google Play / the App Store.
"""
from django.db import migrations

COMMON_CHECKLIST = "\n".join([
    "The recorder (DVR/NVR) is powered on and shows your cameras on its monitor",
    "The recorder is connected to your internet router with a network cable",
    "Your router has working internet (try a website on Wi-Fi at the site)",
    "You have the recorder's admin password, or the device verification code on its label",
    "Your phone has mobile data or Wi-Fi",
])

GUIDES = [
    {
        "title": "Before you start: viewing your CCTV on your phone",
        "brand": "General",
        "app_name": "",
        "summary": "A quick checklist that solves most 'cameras not showing on my phone' problems before you open any app.",
        "before_you_start": COMMON_CHECKLIST,
        "steps": "\n".join([
            "Find your recorder's brand on its front panel or the label underneath (for example Hikvision, Dahua or CP Plus)",
            "Install that brand's official viewing app from Google Play or the App Store (see the brand guides on this page)",
            "Create an account in the app with your mobile number or email and keep the password safe",
            "Add your recorder to the app, usually by scanning the QR code on the recorder's label or in its network/cloud settings",
            "Open the device in the app and tap a camera to see live video; use Playback to watch recordings",
        ]),
        "troubleshooting": "\n".join([
            "Device shows offline: check the recorder's network cable and that the router has internet, then restart the router",
            "Asks for a password or verification code you don't know: check the recorder's label, or raise a service request and we'll help",
            "Device is already added to another account: the first account must remove or share it; contact us if you can't reach that person",
            "Video is slow or keeps buffering: switch to the lower-quality (sub-stream / SD) view in the app",
        ]),
        "order": 0,
    },
    {
        "title": "Hikvision: view cameras with Hik-Connect",
        "brand": "Hikvision",
        "app_name": "Hik-Connect",
        "summary": "Add a Hikvision DVR or NVR to the Hik-Connect app and watch live video and recordings on your phone.",
        "before_you_start": COMMON_CHECKLIST,
        "steps": "\n".join([
            "Install the Hik-Connect app and register an account",
            "On the recorder, open its network settings and make sure Hik-Connect (cloud / platform access) is enabled and shows online",
            "In the app, tap + (Add Device) and choose Scan QR Code",
            "Scan the QR code on the recorder's label, or the QR code shown on the recorder's Hik-Connect settings screen",
            "Enter the device verification code when asked (printed on the label, or set in the recorder's Hik-Connect settings)",
            "Tap the added device to see live view; select a camera and choose Playback for recordings",
        ]),
        "troubleshooting": "\n".join([
            "Device offline in the app: check the recorder shows Hik-Connect as online in its network settings",
            "Verification code rejected: use the code from the recorder's Hik-Connect settings if it was changed from the label",
            "Device already added by another account: that account must delete or share the device",
        ]),
        "order": 10,
    },
    {
        "title": "Dahua: view cameras with DMSS",
        "brand": "Dahua",
        "app_name": "DMSS",
        "summary": "Add a Dahua DVR or NVR to the DMSS app using its serial number QR code (P2P).",
        "before_you_start": COMMON_CHECKLIST,
        "steps": "\n".join([
            "Install the DMSS app and sign in or continue as instructed by the app",
            "On the recorder, open its network settings and make sure P2P is enabled and shows online",
            "In the app, tap + and choose to add a device by scanning its QR code / serial number (SN)",
            "Scan the QR code on the recorder's label or on its P2P settings screen",
            "Enter the recorder's username and password when asked",
            "Open the device to see live view; use Playback to watch recordings",
        ]),
        "troubleshooting": "\n".join([
            "Device offline: check P2P shows online on the recorder and the router has internet",
            "Wrong username or password: use the recorder's admin login, not your app account password",
        ]),
        "order": 20,
    },
    {
        "title": "CP Plus: view cameras with gCMOB",
        "brand": "CP Plus",
        "app_name": "gCMOB",
        "summary": "Add a CP Plus DVR or NVR to the gCMOB app using its P2P serial number QR code.",
        "before_you_start": COMMON_CHECKLIST,
        "steps": "\n".join([
            "Install the gCMOB app",
            "On the recorder, open its network settings and make sure P2P is enabled and shows online",
            "In the app, open the device manager and tap + to add a device using P2P / serial number",
            "Scan the QR code on the recorder's label or its P2P settings screen",
            "Enter the recorder's username and password, save, then open the device to start live view",
        ]),
        "troubleshooting": "\n".join([
            "Device offline: check P2P status on the recorder and the router's internet",
            "Newer CP Plus models may use a different CP Plus app: check the recorder's manual or ask us",
        ]),
        "order": 30,
    },
]


def add_drafts(apps, schema_editor):
    ViewingGuide = apps.get_model("support", "ViewingGuide")
    from django.utils.text import slugify
    for data in GUIDES:
        slug = slugify(data["title"])[:150]
        if not ViewingGuide.objects.filter(slug=slug).exists():
            ViewingGuide.objects.create(slug=slug, is_published=False, **data)


def remove_drafts(apps, schema_editor):
    ViewingGuide = apps.get_model("support", "ViewingGuide")
    from django.utils.text import slugify
    ViewingGuide.objects.filter(slug__in=[slugify(g["title"])[:150] for g in GUIDES], is_published=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0004_viewing_guides"),
    ]

    operations = [
        migrations.RunPython(add_drafts, remove_drafts),
    ]
