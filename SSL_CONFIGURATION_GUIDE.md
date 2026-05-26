# SSL/HTTPS Security Configuration Guide

## Current Status
Your project already has basic SSL configuration in `config/settings.py` but needs enhancement for comprehensive security.

## Required Changes to settings.py

Replace the existing SSL configuration (lines 156-163) with:

```python
# Import SSL/HTTPS Security Settings
from .security_settings import *
```

And remove the existing SSL block:
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', cast=bool, default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', cast=int, default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', cast=bool, default=True)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', cast=bool, default=True)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## Environment Variables (.env file)

Add these to your `.env` file:

```bash
# SSL/HTTPS Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_SSL_HOST=yourdomain.com

# For production (DEBUG=False)
# For development (DEBUG=True), these will be automatically relaxed
```

## Security Features Implemented

### 1. SSL/HTTPS Configuration
- **SECURE_SSL_REDIRECT**: Forces HTTPS in production
- **SECURE_PROXY_SSL_HEADER**: Handles proxy headers (Load balancers/CDNs)
- **SECURE_SSL_HOST**: Optional SSL certificate domain verification

### 2. Secure Cookies
- **SESSION_COOKIE_SECURE**: Cookies only sent over HTTPS
- **CSRF_COOKIE_SECURE**: CSRF cookies only over HTTPS
- **SESSION_COOKIE_HTTPONLY**: Prevents JavaScript access to session cookies
- **CSRF_COOKIE_HTTPONLY**: Prevents JavaScript access to CSRF cookies
- **SESSION_COOKIE_SAMESITE**: Strict same-site policy
- **CSRF_COOKIE_SAMESITE**: Strict same-site policy

### 3. HTTP Strict Transport Security (HSTS)
- **SECURE_HSTS_SECONDS**: 1 year HSTS policy
- **SECURE_HSTS_INCLUDE_SUBDOMAINS**: Applies to all subdomains
- **SECURE_HSTS_PRELOAD**: Enables browser preloading

### 4. Additional Security Headers
- **SECURE_CONTENT_TYPE_NOSNIFF**: Prevents MIME-type sniffing
- **SECURE_BROWSER_XSS_FILTER**: Enables XSS filter in old browsers
- **SECURE_REFERRER_POLICY**: Controls referrer information
- **X_FRAME_OPTIONS**: Prevents clickjacking

## Development vs Production

### Development (DEBUG=True)
- SSL redirects disabled for local development
- Relaxed cookie policies for testing
- HSTS disabled to avoid local HTTPS issues

### Production (DEBUG=False)
- Full SSL enforcement
- Strict security policies
- HSTS enabled for long-term security

## Deployment Checklist

1. **SSL Certificate**: Install valid SSL certificate
2. **Load Balancer/Proxy**: Configure to forward HTTPS headers
3. **Environment Variables**: Set production values in .env
4. **Domain**: Update SECURE_SSL_HOST with your domain
5. **Test**: Verify HTTPS redirects work correctly

## Testing SSL Configuration

```bash
# Test HTTPS redirect
curl -I http://yourdomain.com

# Should return 301 redirect to HTTPS

# Test HSTS
curl -I https://yourdomain.com

# Should include:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

## Security Headers Verification

Check headers using:
```bash
curl -I https://yourdomain.com
```

Expected headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Troubleshooting

### Common Issues
1. **Infinite Redirect Loop**: Check proxy configuration
2. **HSTS Too Strict**: Reduce SECURE_HSTS_SECONDS during testing
3. **Cookie Issues**: Verify domain and SSL configuration

### Debug Mode
Set DEBUG=True temporarily to relax security for troubleshooting.

## Security Benefits

1. **Data Encryption**: All traffic encrypted with SSL/TLS
2. **HSTS Protection**: Prevents SSL stripping attacks
3. **Cookie Security**: Prevents session hijacking
4. **Clickjacking Protection**: Prevents UI redress attacks
5. **XSS Protection**: Additional browser XSS filtering

## Compliance

This configuration helps with:
- GDPR compliance (data protection)
- PCI DSS compliance (payment processing)
- General data security best practices
