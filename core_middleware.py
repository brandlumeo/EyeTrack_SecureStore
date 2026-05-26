from django.utils.cache import add_never_cache_headers

class DisableClientCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response


class CartCleanupMiddleware:
    """Middleware to clean up cart session data and prevent showing 1 without items"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
        else:
            # Ensure cart is always initialized as empty dict
            request.session['cart'] = {}
        
        response = self.get_response(request)
        return response
