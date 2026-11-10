import json
import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import QuoteRequestForm
from .models import FAQCategory, FAQ, QuoteRequest

logger = logging.getLogger(__name__)

def faq_view(request):
    faq_categories = FAQCategory.objects.prefetch_related('faqs').all()
    # If no categories exist, provide some defaults for the first visit
    if not faq_categories.exists():
        _create_default_faqs()
        faq_categories = FAQCategory.objects.prefetch_related('faqs').all()
    
    return render(request, 'support/faq.html', {'faq_categories': faq_categories})

def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            
            # Simple AI Logic (Keyword Based)
            response = _get_chatbot_response(user_message)
            
            return JsonResponse({'message': response})
        except Exception as e:
            return JsonResponse({'message': "I'm sorry, I encountered an error. How else can I help?"}, status=400)
    return JsonResponse({'message': 'Invalid request'}, status=405)

def _get_chatbot_response(message):
    # Keywords for "Will this work with my DVR?"
    dvr_keywords = ['dvr', 'compatible', 'work with', 'connect', 'supported']
    installation_keywords = ['install', 'setup', 'service', 'technician']
    shipping_keywords = ['shipping', 'delivery', 'status', 'track']
    price_keywords = ['price', 'cost', 'discount', 'offer']
    
    if any(k in message for k in dvr_keywords):
        return ("Most of our HD cameras use standard BNC connectors and are compatible with Hikvision, CP PLUS, and Dahua DVRs. "
                "For IP cameras, ensure your NVR supports ONVIF. Do you have a specific model in mind?")
    
    if any(k in message for k in installation_keywords):
        return ("Yes! We provide professional installation services in selected areas. "
                "You can toggle 'Add Installation Service' on the product page. Would you like to check serviceability for your pincode?")
    
    if any(k in message for k in shipping_keywords):
        return ("Standard delivery takes 3-5 business days. Once shipped, you'll receive a tracking link via email. "
                "You can also track your order in the 'Orders' section of your account.")
    
    if any(k in message for k in price_keywords):
        return ("We offer competitive pricing on all premium security gear. "
                "Check out our 'Special Offers' section for the latest discounts!")

    if 'hello' in message or 'hi' in message:
        return "Hello! I'm your EyeTrack Assistant. How can I help you secure your space today?"

    return ("I'm still learning! You can ask about DVR compatibility, installation services, or order tracking. "
            "For more complex queries, feel free to visit our FAQ page or contact our human support.")

def _create_default_faqs():
    # Helper to seed some initial data
    cat_general, _ = FAQCategory.objects.get_or_create(name="General", icon="bi-info-circle", order=1)
    cat_orders, _ = FAQCategory.objects.get_or_create(name="Orders & Shipping", icon="bi-truck", order=2)
    cat_tech, _ = FAQCategory.objects.get_or_create(name="Technical Support", icon="bi-cpu", order=3)

    FAQ.objects.get_or_create(
        category=cat_tech,
        question="Will these cameras work with my existing DVR?",
        answer="Our HD-Analog cameras are compatible with most modern DVRs (Hikvision, CP PLUS, Dahua, etc.) that support AHD/TVI/CVI signals. IP cameras require an ONVIF-compliant NVR.",
        order=1
    )
    FAQ.objects.get_or_create(
        category=cat_orders,
        question="How long does delivery take?",
        answer="Orders are typically processed within 24 hours and delivered within 3-5 business days depending on your location.",
        order=1
    )
    FAQ.objects.get_or_create(
        category=cat_general,
        question="Do you provide installation?",
        answer="Yes, we offer professional installation services. You can select this option during checkout for eligible products.",
        order=1
    )


def _quote_summary(lead):
    lines = [
        f"Name: {lead.name}",
        f"Phone: {lead.phone}",
        f"Site: {lead.get_site_type_display()}",
        f"Cameras: {lead.get_camera_count_display()}",
    ]
    if lead.package:
        lines.append(f"Package: {lead.package}")
    if lead.location or lead.pincode:
        lines.append(f"Location: {' '.join(filter(None, [lead.location, lead.pincode]))}")
    if lead.email:
        lines.append(f"Email: {lead.email}")
    if lead.message:
        lines.append(f"Notes: {lead.message}")
    return "\n".join(lines)


def _notify_staff_of_quote(lead, admin_url):
    """Email the configured admins and drop a bell notification for staff users."""
    from accounts.models import Notification

    summary = _quote_summary(lead)
    recipients = [email for _, email in getattr(settings, "ADMINS", []) if email]
    if recipients:
        try:
            send_mail(
                subject=f"New site survey request: {lead.name} ({lead.get_site_type_display()})",
                message=f"{summary}\n\nManage lead: {admin_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send quote request email for lead %s", lead.pk)

    for user in get_user_model().objects.filter(is_staff=True, is_active=True):
        Notification.send(
            user=user,
            title="New site survey request",
            message=f"{lead.name} - {lead.get_site_type_display()}, {lead.get_camera_count_display()}",
            link=reverse("admin_dashboard:quote_requests"),
        )


@require_http_methods(["GET", "POST"])
def quote_request(request):
    wants_json = request.headers.get("x-requested-with") == "XMLHttpRequest"
    initial = {
        key: request.GET[key]
        for key in ("site_type", "camera_count", "package")
        if request.GET.get(key)
    }
    form = QuoteRequestForm(request.POST or None, initial=initial)

    if request.method == "POST":
        if form.is_valid() and not form.cleaned_data.get("website"):
            lead = form.save(commit=False)
            lead.source_page = request.META.get("HTTP_REFERER", "")[:255]
            lead.save()

            admin_url = request.build_absolute_uri(reverse("admin_dashboard:quote_requests"))
            from orders.emails import send_email_async
            send_email_async(_notify_staff_of_quote, lead, admin_url)

            whatsapp_text = "Hi Eyetrack, I just requested a free site survey.\n" + _quote_summary(lead)
            whatsapp_url = f"https://wa.me/{settings.BUSINESS_WHATSAPP}?text={quote(whatsapp_text)}"
            if wants_json:
                return JsonResponse({"ok": True, "whatsapp_url": whatsapp_url, "name": lead.name})
            messages.success(request, f"Thanks {lead.name}! Our team will call you shortly to plan your free site survey.")
            request.session["quote_whatsapp_url"] = whatsapp_url
            return redirect("quote_request")
        if wants_json:
            return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    return render(request, "support/quote_request.html", {
        "form": form,
        "whatsapp_url": request.session.pop("quote_whatsapp_url", None),
    })
