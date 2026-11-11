from django.db.models import Count, Q
from .models import Category, Product


def cart_count(request):
    """Calculate cart count from session, validating that products still exist and are available."""
    cart = request.session.get('cart', {})
    
    # Ensure cart is a dictionary
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
        request.session.modified = True
    
    # Get all valid product IDs from the cart that exist and are available
    valid_product_ids = []
    total_quantity = 0
    
    for product_id_str, qty in cart.items():
        try:
            product_id = int(product_id_str)
            # Verify product exists and is available
            product = Product.objects.filter(id=product_id, is_available=True).exists()
            if product and isinstance(qty, (int, float)) and qty > 0:
                valid_product_ids.append(product_id_str)
                total_quantity += int(qty)
        except (ValueError, TypeError):
            # Invalid product_id or quantity, skip it
            continue
    
    # Clean up session if there are invalid items
    if len(valid_product_ids) != len(cart):
        cleaned_cart = {pid: cart[pid] for pid in valid_product_ids}
        request.session['cart'] = cleaned_cart
        request.session.modified = True
    
    return {
        'cart_count': total_quantity
    }


def wishlist_count(request):
    """Expose the logged-in user's wishlist item count globally (0 for guests)."""
    if not request.user.is_authenticated:
        return {'wishlist_count': 0}
    from .models import Wishlist  # local import avoids circular dependency
    count = Wishlist.objects.filter(user=request.user).count()
    return {'wishlist_count': count}


def categories(request):
    """Make all categories available in every template"""
    # Define the precise requested order for the navbar dropdown
    order = [
        "CCTV Cameras",
        "Biometric Devices",
        "Video Door Phones",
        "Smart Locks",
        "Access Control",
        "Alarm Systems",
        "Laptops",
    ]
    
    # Only fetch the categories that match our explicit service lines
    cats = list(Category.objects.filter(name__in=order).annotate(
        product_count=Count('products', filter=Q(products__is_available=True))
    ))
    
    # Sort categories based on their exact index in the target order
    cats.sort(key=lambda x: order.index(x.name))
    
    return {
        'categories': cats
    }

def firebase_config(request):
    """Exposes Firebase credentials to the frontend from settings (env)."""
    from django.conf import settings
    return {
        "FIREBASE_CONFIG_JSON": {
            "apiKey": settings.FIREBASE_API_KEY,
            "authDomain": settings.FIREBASE_AUTH_DOMAIN,
            "projectId": settings.FIREBASE_PROJECT_ID,
            "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
            "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
            "appId": settings.FIREBASE_APP_ID,
            "measurementId": settings.FIREBASE_MEASUREMENT_ID,
            "vapidKey": settings.FIREBASE_VAPID_KEY,
        },
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    }


def business_contact(request):
    """Expose the business phone / WhatsApp numbers used by contact CTAs."""
    from django.conf import settings
    return {
        "BUSINESS_PHONE": settings.BUSINESS_PHONE,
        "BUSINESS_WHATSAPP": settings.BUSINESS_WHATSAPP,
    }
