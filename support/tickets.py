"""Shared logic for service tickets: photo uploads and notifications (used by customer and staff views)."""
import logging

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)

MAX_PHOTOS = 5
MAX_PHOTO_MB = 8


def validate_photos(files):
    """Return (valid_images, errors) for an <input type=file multiple> upload."""
    field = forms.ImageField()
    valid, errors = [], []
    if len(files) > MAX_PHOTOS:
        errors.append("Only the first %d photos were added." % MAX_PHOTOS)
        files = files[:MAX_PHOTOS]
    for f in files:
        if f.size > MAX_PHOTO_MB * 1024 * 1024:
            errors.append("%s is larger than %d MB." % (f.name, MAX_PHOTO_MB))
            continue
        try:
            valid.append(field.clean(f))
        except forms.ValidationError:
            errors.append("%s is not a valid image." % f.name)
    return valid, errors


def save_photos(ticket, files, message=None):
    for upload in files:
        ticket.attachments.create(image=upload, message=message)


def _email(subject, body, recipients):
    if not recipients:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:
        logger.exception("Failed to send service ticket email: %s", subject)


def _send_async(subject, body, recipients):
    from orders.emails import send_email_async
    send_email_async(_email, subject, body, recipients)


def notify_staff(ticket, title, message, request=None):
    """Bell notification for every active staff user, plus an email to the configured admins."""
    from accounts.models import Notification

    link = reverse("admin_dashboard:ticket_manage", args=[ticket.pk])
    for user in get_user_model().objects.filter(is_staff=True, is_active=True):
        Notification.send(user=user, title=title, message=message, link=link)
    url = request.build_absolute_uri(link) if request else link
    recipients = [email for _, email in getattr(settings, "ADMINS", []) if email]
    _send_async("%s: %s" % (title, ticket.reference), "%s\n\n%s\n\nOpen: %s" % (message, ticket.subject, url), recipients)


def notify_customer(ticket, title, message, request=None):
    """Bell notification and email to the customer who raised the ticket."""
    from accounts.models import Notification

    link = reverse("ticket_detail", args=[ticket.pk])
    Notification.send(user=ticket.user, title=title, message=message, link=link)
    url = request.build_absolute_uri(link) if request else link
    if ticket.user.email:
        _send_async(
            "%s - %s (Eyetrack Solutions)" % (title, ticket.reference),
            "Hello %s,\n\n%s\n\nView your request: %s\n\nEyetrack Solutions"
            % (ticket.user.first_name or ticket.user.get_username(), message, url),
            [ticket.user.email],
        )
