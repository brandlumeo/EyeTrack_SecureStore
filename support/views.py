from django.shortcuts import render
from django.http import JsonResponse
from .models import FAQCategory, FAQ
import json

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
