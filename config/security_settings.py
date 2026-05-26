"""
SSL/HTTPS Security Configuration for EyeTrack_SecureStore
This module contains comprehensive security settings for production deployment
"""

from decouple import config

# SSL/HTTPS Security Settings
def get_security_settings():
    """Returns security settings based on DEBUG mode"""
    DEBUG = config('DEBUG', cast=bool, default=False)
    
    if not DEBUG:
        return {
            # SSL/HTTPS Configuration
            'SECURE_SSL_REDIRECT': config('SECURE_SSL_REDIRECT', cast=bool, default=True),
            'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
            
            # Secure Cookies
            'SESSION_COOKIE_SECURE': True,
            'CSRF_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'CSRF_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'CSRF_COOKIE_SAMESITE': 'Strict',
            
            # HTTP Strict Transport Security (HSTS)
            'SECURE_HSTS_SECONDS': config('SECURE_HSTS_SECONDS', cast=int, default=31536000),  # 1 year
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': config('SECURE_HSTS_INCLUDE_SUBDOMAINS', cast=bool, default=True),
            'SECURE_HSTS_PRELOAD': config('SECURE_HSTS_PRELOAD', cast=bool, default=True),
            
            # Additional Security Headers
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_BROWSER_XSS_FILTER': True,
            'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
            'X_FRAME_OPTIONS': 'DENY',

            # Allow Firebase/Google OAuth popup to communicate with main window.
            # Must be 'same-origin-allow-popups' — 'same-origin' breaks signInWithPopup.
            'SECURE_CROSS_ORIGIN_OPENER_POLICY': 'same-origin-allow-popups',
            
            # SSL Certificate Configuration
            'SECURE_SSL_HOST': config('SECURE_SSL_HOST', default=None),
        }
    else:
        # Development settings - relax security for local development
        return {
            'SECURE_SSL_REDIRECT': False,
            'SESSION_COOKIE_SECURE': False,
            'CSRF_COOKIE_SECURE': False,
            'SECURE_HSTS_SECONDS': 0,
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': False,
            'SECURE_HSTS_PRELOAD': False,
            'SECURE_PROXY_SSL_HEADER': None,
            'SESSION_COOKIE_HTTPONLY': True,  # Keep this for security
            'CSRF_COOKIE_HTTPONLY': True,     # Keep this for security
            'SESSION_COOKIE_SAMESITE': 'Lax', # More permissive for development
            'CSRF_COOKIE_SAMESITE': 'Lax',
            'SECURE_CROSS_ORIGIN_OPENER_POLICY': 'same-origin-allow-popups',
        }

# Apply security settings to globals()
security_config = get_security_settings()
for key, value in security_config.items():
    globals()[key] = value
