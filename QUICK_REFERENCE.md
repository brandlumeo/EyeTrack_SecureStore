# Quick Reference Guide - EyeTrack Solutions

## 🚀 Quick Start Commands

```bash
# 1. Apply migrations to create categories
python manage.py migrate store

# 2. Add sample products
python manage.py add_sample_products

# 3. Run development server
python manage.py runserver

# 4. Access store
# Browser: http://localhost:8000
# Admin: http://localhost:8000/admin/
```

---

## 📁 Project Structure

```
EyeTrack_SecureStore/
├── manage.py
├── requirements.txt
├── STORE_SETUP_GUIDE.md          # Full setup documentation
├── IMPLEMENTATION_SUMMARY.md     # What was implemented
├── QUICK_REFERENCE.md            # This file
│
├── config/
│   ├── settings.py               # Django settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── store/
│   ├── models.py                 # Category, Product models
│   ├── views.py                  # All store views
│   ├── urls.py                   # Store URLs
│   ├── admin.py                  # Django admin config
│   ├── context_processors.py     # cart_count, categories
│   │
│   ├── management/
│   │   └── commands/
│   │       └── add_sample_products.py  # 📌 Add products here
│   │
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_product_specs.py
│       └── 0003_add_service_categories.py  # 📌 Categories migration
│
├── accounts/
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── orders/
│   ├── models.py
│   └── migrations/
│
├── static/
│   ├── css/
│   │   └── site.css              # 📌 Update for styling
│   ├── js/
│   │   └── site.js               # 📌 Update for features
│   └── img/
│       └── company-logo.png
│
├── media/
│   └── products/                 # 📌 Product images here
│
└── templates/
    ├── base.html                 # 📌 Main layout (dropdown added)
    ├── home.html
    ├── store/
    │   ├── product_list.html
    │   ├── product_detail.html
    │   ├── compare.html
    │   └── cart.html
    └── accounts/
        ├── login.html
        └── register.html
```

---

## 🔑 Key Files to Modify

### Add New Products
📄 **File**: `store/management/commands/add_sample_products.py`

```python
# Add to products_data list:
{
    'name': 'Product Name',
    'category_slug': 'category-slug',
    'description': 'Description here',
    'price': Decimal('9999.00'),
    'stock': 10,
    'is_available': True,
}
```

### Add New Category
📄 **File**: `store/migrations/0003_add_service_categories.py`

```python
# Add to categories_data list:
{
    'name': 'New Category',
    'slug': 'new-category'
}
```

Then run:
```bash
python manage.py migrate store
```

### Edit Navigation Menu
📄 **File**: `templates/base.html` (Line ~95-130)

```html
<li><a class="dropdown-item" href="{% url 'products_by_category' 'category-slug' %}">
    <i class="bi bi-icon me-2"></i>Category Name
</a></li>
```

### Update Styles
📄 **File**: `static/css/site.css` (Last section)

All dropdown styling is here. Modify colors, spacing, etc.

### Add Features
📄 **File**: `static/js/site.js`

JavaScript for cart, comparison, wishlist features.

---

## 📊 Database Models

### Category
```python
- id (Primary Key)
- name (CharField, max 200)
- slug (SlugField, unique)
```

### Product
```python
- id (Primary Key)
- category (ForeignKey → Category)
- name (CharField, max 255)
- slug (SlugField, unique)
- description (TextField)
- camera_type (CharField - choices)
- resolution_mp (DecimalField)
- price (DecimalField)
- stock (PositiveIntegerField)
- image (ImageField)
- warranty_years (PositiveSmallIntegerField)
- is_available (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
- ... and more technical specs
```

---

## 🔗 Important URLs

### Frontend
- **Home**: `/`
- **Shop**: `/`
- **Category**: `/category/dome-cameras/`
- **Product**: `/product/hikvision-dome-2mp/`
- **Cart**: `/cart/`
- **Compare**: `/compare/`
- **Wishlist**: `/wishlist/`

### Admin
- **Dashboard**: `/admin/`
- **Categories**: `/admin/store/category/`
- **Products**: `/admin/store/product/`
- **Orders**: `/admin/orders/order/`

### API
- **Quick View**: `/api/product/{id}/quick-view/`
- **Validate Compare**: `/api/validate-compare/`

---

## 🎨 Categories List

```
1. Dome Cameras       → dome-cameras
2. Bullet Cameras     → bullet-cameras
3. PTZ Cameras        → ptz-cameras
4. DVR Systems        → dvr-systems
5. NVR Systems        → nvr-systems
6. Smart Locks        → smart-locks
7. Biometric Devices  → biometric-devices
8. Home/Gate Auto     → home-gate-automation
9. Other Products     → other-security-products
10. CCTV Services     → cctv-installations
```

---

## 💾 Database Commands

```bash
# Show migration status
python manage.py showmigrations store

# Apply specific migration
python manage.py migrate store 0003_add_service_categories

# Rollback migration
python manage.py migrate store 0002_product_specs

# Create shell for testing
python manage.py shell
```

---

## 🛠 Django Admin Tips

### Add Product via Admin:
1. Go to `/admin/store/product/`
2. Click "Add Product +"
3. Fill in details:
   - Category (dropdown)
   - Name
   - Price (in rupees)
   - Stock (quantity)
   - Image (upload)
   - Technical specs (if camera)
4. Save

### Edit Category:
1. Go to `/admin/store/category/`
2. Click category name
3. Change name/slug
4. Save

### View Product Count:
- Admin shows product count next to each category
- Example: "Dome Cameras (3 products)"

---

## 🚨 Common Issues & Fixes

**Categories not visible?**
```bash
python manage.py migrate store
python manage.py runserver
# Refresh browser
```

**Products command fails?**
```bash
# Check if files exist:
# store/management/__init__.py
# store/management/commands/__init__.py
# store/management/commands/add_sample_products.py

# Then run:
python manage.py add_sample_products
```

**Cart shows wrong count?**
```python
# Check context_processors.py
# Should filter for qty > 0

def cart_count(request):
    cart = request.session.get('cart', {})
    total_items = sum(int(qty) for qty in cart.values() 
                     if isinstance(qty, (int, float)) and qty > 0)
    return {'cart_count': total_items}
```

---

## 📱 Mobile Testing

Use these viewport sizes:
- **Mobile**: 375px (iPhone)
- **Tablet**: 768px (iPad)
- **Desktop**: 1200px

All features responsive with Bootstrap.

---

## 🔐 Security Checklist

✅ CSRF protection enabled
✅ Session security configured
✅ Debug mode off in production
✅ Allowed hosts configured
✅ Secret key in environment

---

## 📈 Performance Tips

1. Use `select_related()` for category lookups
2. Add database indexes on frequently queried fields
3. Cache category list in context processor
4. Lazy load product images
5. Minify CSS/JS in production

---

## 🎯 Next Development Tasks

1. **Payment Integration**
   - Stripe/PayPal setup
   - Order payment tracking

2. **Search & Filters**
   - Price range filter
   - Specification filters

3. **Reviews & Ratings**
   - Product reviews
   - User ratings

4. **Notifications**
   - Email on order
   - Stock alerts

5. **Analytics**
   - Product views
   - Conversion tracking

---

## 📞 Quick Support

**For Questions:**
- Check `STORE_SETUP_GUIDE.md`
- Review model definitions in `store/models.py`
- Look at existing views in `store/views.py`
- Check admin.py for customization options

**For New Features:**
- Model changes: `store/models.py`
- View logic: `store/views.py`
- URLs: `store/urls.py`
- Admin: `store/admin.py`
- Templates: `templates/store/`

---

**Happy Coding! 🚀**

Your EyeTrack Solutions store is ready for development.
