# SSL/HTTPS Deployment Checklist

## Pre-Deployment Checklist

### 1. SSL Certificate Setup
- [ ] Install valid SSL certificate on your domain
- [ ] Verify certificate covers all subdomains (wildcard or SAN)
- [ ] Check certificate expiration date
- [ ] Test certificate chain completeness

### 2. Server Configuration
- [ ] Configure web server (Nginx/Apache) for SSL termination
- [ ] Set up proper SSL cipher suites
- [ ] Enable HTTP/2 with SSL
- [ ] Configure redirect from HTTP to HTTPS
- [ ] Set up proxy headers if using load balancer

### 3. Django Settings Update
- [ ] Update `config/settings.py` to import security settings
- [ ] Add environment variables to `.env` file
- [ ] Set `DEBUG=False` in production
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Configure `CSRF_TRUSTED_ORIGINS` with HTTPS URLs

### 4. Middleware Configuration
- [ ] Add custom security middleware to settings
- [ ] Update middleware order if needed
- [ ] Test middleware functionality

## Environment Variables Configuration

Add to your production `.env` file:

```bash
# Production Settings
DEBUG=False
SECRET_KEY=your-super-secret-production-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL/HTTPS Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_SSL_HOST=yourdomain.com

# Database (use production credentials)
DB_NAME=production_db
DB_USER=production_user
DB_PASSWORD=secure_password
DB_HOST=your-db-host
DB_PORT=5432

# Email (production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
```

## Web Server Configuration Examples

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    SSLEngine on
    SSLCertificateFile /path/to/your/certificate.crt
    SSLCertificateKeyFile /path/to/your/private.key

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    RequestHeader set X-Forwarded-Proto "https"
</VirtualHost>
```

## Post-Deployment Testing

### 1. SSL Certificate Testing
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check SSL rating
curl -I https://yourdomain.com
```

### 2. Security Headers Testing
```bash
# Check security headers
curl -I https://yourdomain.com

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: default-src 'self'...
```

### 3. HTTPS Redirect Testing
```bash
# Test HTTP to HTTPS redirect
curl -I http://yourdomain.com

# Should return 301 redirect to HTTPS
```

### 4. Django Admin Access
- [ ] Verify admin panel works over HTTPS
- [ ] Test login functionality
- [ ] Check secure cookies in browser dev tools

### 5. Ecommerce Functionality
- [ ] Test checkout process over HTTPS
- [ ] Verify payment processing (if implemented)
- [ ] Check user registration/login
- [ ] Test cart functionality

## Security Validation Tools

### Online SSL Testers
- [ ] SSL Labs Test: https://www.ssllabs.com/ssltest/
- [ ] Security Headers Test: https://securityheaders.com/
- [ ] Observatory by Mozilla: https://observatory.mozilla.org/

### Command Line Tools
```bash
# Test with testssl.sh
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh https://yourdomain.com

# Check HSTS preload status
curl -s https://hstspreload.org/api/v2/status?domain=yourdomain.com
```

## Troubleshooting Guide

### Common Issues

#### 1. Infinite Redirect Loop
**Cause**: Misconfigured proxy headers or SSL redirect
**Solution**: Check `SECURE_PROXY_SSL_HEADER` and web server configuration

#### 2. HSTS Too Strict
**Cause**: HSTS preventing access during testing
**Solution**: Clear browser HSTS cache or reduce `SECURE_HSTS_SECONDS`

#### 3. Mixed Content Warnings
**Cause**: HTTP resources on HTTPS page
**Solution**: Update all resource URLs to HTTPS or protocol-relative

#### 4. Admin Panel Not Accessible
**Cause**: Security headers blocking admin functionality
**Solution**: Adjust CSP policy or add exceptions for admin paths

### Debug Mode for SSL Issues

Temporarily enable debug mode:
```python
# In settings.py
DEBUG = True  # Only for debugging
```

Or create a debug SSL settings file:
```python
# debug_ssl_settings.py
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
```

## Ongoing Maintenance

### Monthly Tasks
- [ ] Check SSL certificate expiration
- [ ] Monitor SSL Labs rating
- [ ] Review security headers
- [ ] Check for SSL vulnerabilities

### Quarterly Tasks
- [ ] Update SSL cipher suites
- [ ] Review HSTS policy
- [ ] Test security configuration
- [ ] Update security middleware

## Compliance Checklist

### PCI DSS Compliance
- [ ] Strong cryptography (TLS 1.2+)
- [ ] Secure transmission of cardholder data
- [ ] Regular monitoring of security controls
- [ ] Secure network architecture

### GDPR Compliance
- [ ] Data encryption in transit
- [ ] Secure data transmission
- [ ] Privacy by design principles
- [ ] Data protection measures

## Emergency Procedures

### SSL Certificate Expiration
1. Obtain new certificate from CA
2. Update web server configuration
3. Reload web server
4. Test SSL functionality
5. Monitor for issues

### Security Breach Response
1. Identify and contain breach
2. Assess impact
3. Notify affected parties
4. Implement additional security measures
5. Document and learn from incident

## Support Contacts

Keep these contacts handy:
- SSL Certificate Provider
- Web Hosting Support
- Security Team Contacts
- Django Security Resources
