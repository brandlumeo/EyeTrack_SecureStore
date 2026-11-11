from django.conf import settings
from django.utils.cache import add_never_cache_headers


def is_media_request(request):
    return request.path.startswith(settings.MEDIA_URL)


class DisableClientCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Uploaded images never change under the same name; let browsers cache them (see config.urls).
        if not is_media_request(request):
            add_never_cache_headers(response)
        return response


class CartCleanupMiddleware:
    """Middleware to clean up cart session data and prevent showing 1 without items"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_media_request(request):
            return self.get_response(request)

        # Clean cart data if it exists and is invalid
        cart = request.session.get('cart', {})
        
        if cart:
            # Ensure it's a dictionary
            if not isinstance(cart, dict):
                request.session['cart'] = {}
                request.session.modified = True
            else:
                # Remove entries with zero or negative quantities
                cleaned_cart = {k: v for k, v in cart.items() 
                               if isinstance(v, (int, float)) and int(v) > 0}
                
                # If cart was modified, update session
                if len(cleaned_cart) != len(cart):
                    request.session['cart'] = cleaned_cart
                    request.session.modified = True
        # No else: writing an empty cart into every new session saved a session row (and set a cookie)
        # for each anonymous page view and bot hit. Cart code reads it with .get('cart', {}).

        response = self.get_response(request)
        return response
