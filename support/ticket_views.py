"""Customer side of service requests (after-sales support tickets)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.views import build_account_context

from .forms import ServiceTicketForm, TicketReplyForm
from .models import ServiceTicket, ViewingGuide
from .tickets import notify_staff, save_photos, validate_photos


def _render(request, template, extra):
    context = build_account_context(request.user)
    context.update(extra)
    return render(request, template, context)


@login_required(login_url="login")
def ticket_list(request):
    tickets = request.user.service_tickets.select_related("order").order_by("-updated_at")
    return _render(request, "support/tickets/list.html", {
        "tickets": tickets,
        "open_count": sum(1 for t in tickets if t.is_open),
    })


@login_required(login_url="login")
def ticket_create(request):
    initial = {"contact_phone": getattr(getattr(request.user, "profile", None), "phone_number", "") or ""}
    order_id = request.GET.get("order", "")
    if order_id.isdigit() and request.user.orders.filter(pk=order_id).exists():
        initial["order"] = int(order_id)
    form = ServiceTicketForm(request.POST or None, user=request.user, initial=initial)

    if request.method == "POST" and form.is_valid():
        photos, photo_errors = validate_photos(request.FILES.getlist("photos"))
        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.save()
        save_photos(ticket, photos)
        for error in photo_errors:
            messages.warning(request, "Photo skipped: %s" % error)
        notify_staff(ticket, "New service request", "%s: %s (%s)" % (
            request.user.get_full_name() or request.user.get_username(), ticket.subject, ticket.get_category_display()), request)
        messages.success(request, "Request %s received. Our support team will get back to you here." % ticket.reference)
        return redirect("ticket_detail", pk=ticket.pk)

    return _render(request, "support/tickets/new.html", {
        "form": form,
        "has_guides": ViewingGuide.objects.filter(is_published=True).exists(),
    })


@login_required(login_url="login")
def ticket_detail(request, pk):
    ticket = get_object_or_404(
        ServiceTicket.objects.select_related("order", "assigned_technician").prefetch_related("messages__author", "attachments"),
        pk=pk, user=request.user,
    )
    form = TicketReplyForm(request.POST or None)
    if request.method == "POST":
        if ticket.status == ServiceTicket.Status.CLOSED:
            messages.error(request, "This request is closed. Please raise a new one if you still need help.")
            return redirect("ticket_detail", pk=ticket.pk)
        if form.is_valid():
            photos, photo_errors = validate_photos(request.FILES.getlist("photos"))
            message = ticket.messages.create(author=request.user, from_staff=False, body=form.cleaned_data["body"])
            save_photos(ticket, photos, message=message)
            for error in photo_errors:
                messages.warning(request, "Photo skipped: %s" % error)
            # A customer reply puts the ticket back in the team's queue.
            if ticket.status in (ServiceTicket.Status.WAITING_CUSTOMER, ServiceTicket.Status.RESOLVED):
                ticket.status = ServiceTicket.Status.OPEN
            ticket.save(update_fields=["status", "updated_at"])
            notify_staff(ticket, "Customer replied", "%s replied on %s" % (
                request.user.get_full_name() or request.user.get_username(), ticket.reference), request)
            messages.success(request, "Reply sent.")
            return redirect("ticket_detail", pk=ticket.pk)

    return _render(request, "support/tickets/detail.html", {
        "ticket": ticket,
        "form": form,
        "intro_photos": [a for a in ticket.attachments.all() if a.message_id is None],
        "show_guides": ticket.category == ServiceTicket.Category.MOBILE_VIEW
                       and ViewingGuide.objects.filter(is_published=True).exists(),
    })


@login_required(login_url="login")
@require_POST
def ticket_close(request, pk):
    ticket = get_object_or_404(ServiceTicket, pk=pk, user=request.user)
    if ticket.status != ServiceTicket.Status.CLOSED:
        ticket.status = ServiceTicket.Status.CLOSED
        ticket.closed_at = timezone.now()
        ticket.save(update_fields=["status", "closed_at", "updated_at"])
        notify_staff(ticket, "Request closed by customer", "%s was closed by the customer" % ticket.reference, request)
        messages.success(request, "Request %s closed. Thank you!" % ticket.reference)
    return redirect("ticket_detail", pk=ticket.pk)
