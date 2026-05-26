"""
Custom Security Middleware for EyeTrack_SecureStore
Additional security middleware for enhanced SSL/HTTPS protection
"""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class SSLRedirectMiddleware:
    """
    Middleware to enforce SSL/HTTPS redirects with additional security headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not request.is_secure() and getattr(settings, 'SECURE_SSL_REDIRECT', False):
            # Only redirect in production
            if not settings.DEBUG:
                host = request.get_host()
                path = request.get_full_path()
                https_url = f'https://{host}{path}'
                return HttpResponsePermanentRedirect(https_url)
        
        response = self.get_response(request)
        
        # Add additional security headers
        if not settings.DEBUG:
            self._add_security_headers(request, response)
        
        return response
    
    def _add_security_headers(self, request, response):
        """Add additional security headers to response"""
        
        # Content Security Policy — includes all domains needed for Firebase + Google auth
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://www.gstatic.com https://apis.google.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com",
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "connect-src 'self' https://firestore.googleapis.com https://www.googleapis.com https://securetoken.googleapis.com https://identitytoolkit.googleapis.com https://fcmregistrations.googleapis.com https://firebase.googleapis.com",
            "frame-src 'self' https://eyetrack-store.firebaseapp.com https://accounts.google.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # CRITICAL: Allow Google sign-in popup to communicate with the main window.
        # 'same-origin-allow-popups' lets popups opened from this page post messages back.
        response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        
        # Permissions Policy (formerly Feature Policy)
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        # Additional security headers
        response['X-XSS-Protection'] = '1; mode=block'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Remove server information
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)


class SecurityHeadersMiddleware:
    """
    Middleware to add comprehensive security headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if not settings.DEBUG:
            self._add_security_headers(request, response)
        
        return response
    
    def _add_security_headers(self, request, response):
        """Add security headers to all responses"""
        
        # Ensure Django's security settings are applied
        if getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            response['X-Content-Type-Options'] = 'nosniff'
        
        if getattr(settings, 'X_FRAME_OPTIONS', None) == 'DENY':
            response['X-Frame-Options'] = 'DENY'
        
        # Add cache control for sensitive pages
        if 'admin' in request.path or 'account' in request.path or 'checkout' in request.path:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'


class RateLimitMiddleware:
    """
    Basic rate limiting middleware for API endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
    
    def __call__(self, request):
        # Rate limit API endpoints
        if '/api/' in request.path or request.path.startswith('/live-search'):
            client_ip = self._get_client_ip(request)
            
            if self._is_rate_limited(client_ip):
                from django.http import HttpResponse
                return HttpResponse('Rate limit exceeded', status=429)
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def _is_rate_limited(self, client_ip, limit=100, window=3600):
        """Basic rate limiting - 100 requests per hour per IP"""
        import time
        
        now = time.time()
        window_start = now - window
        
        # Clean old entries
        self.request_counts = {
            ip: requests for ip, requests in self.request_counts.items()
            if any(timestamp > window_start for timestamp in requests)
        }
        
        # Check current IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Count requests in window
        recent_requests = [req_time for req_time in self.request_counts[client_ip] if req_time > window_start]
        
        if len(recent_requests) >= limit:
            return True
        
        # Add current request
        self.request_counts[client_ip].append(now)
        return False
