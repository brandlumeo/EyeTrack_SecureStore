# 🏗️ EyeTrack Solutions - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB BROWSER (User Interface)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Navigation Menu (Shop Dropdown)                         │   │
│  │  ├─ Dome Cameras                                         │   │
│  │  ├─ Bullet Cameras                                       │   │
│  │  ├─ PTZ Cameras                                          │   │
│  │  ├─ DVR Systems                                          │   │
│  │  ├─ NVR Systems                                          │   │
│  │  ├─ Smart Locks                                          │   │
│  │  ├─ Biometric Devices                                    │   │
│  │  ├─ Home/Gate Automation                                 │   │
│  │  └─ CCTV Installations (Service)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Product Pages | Compare | Cart | Wishlist              │   │
│  │  ├─ Product Listing (by category)                        │   │
│  │  ├─ Product Details (with specs)                         │   │
│  │  ├─ Compare Tool (same category only)                    │   │
│  │  ├─ Shopping Cart (session-based)                        │   │
│  │  └─ Wishlist (local storage)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/AJAX
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO BACKEND (Server)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  URL Routes (store/urls.py)                              │   │
│  │  ├─ / → product_list()                                   │   │
│  │  ├─ /category/<slug>/ → product_list()                   │   │
│  │  ├─ /product/<slug>/ → product_detail()                  │   │
│  │  ├─ /api/product/<id>/quick-view/ → quick_view()        │   │
│  │  ├─ /api/validate-compare/ → validate_compare()         │   │
│  │  ├─ /cart/ → cart_view()                                 │   │
│  │  ├─ /compare/ → compare_page()                           │   │
│  │  └─ /admin/ → Django Admin                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Views (store/views.py)                                  │   │
│  │  ├─ product_list()        → Get categories & products    │   │
│  │  ├─ product_detail()      → Show single product          │   │
│  │  ├─ quick_view_product()  → Return JSON for modal        │   │
│  │  ├─ add_to_cart()         → Manage session cart          │   │
│  │  ├─ cart_view()           → Display cart page            │   │
│  │  ├─ compare_page()        → Show comparison              │   │
│  │  └─ validate_compare()    → Check category match         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Context Processors (store/context_processors.py)        │   │
│  │  ├─ cart_count()    → Calculate items in cart            │   │
│  │  └─ categories()    → Load all categories                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Middleware (core_middleware.py)                         │   │
│  │  ├─ DisableClientCacheMiddleware                         │   │
│  │  └─ CartCleanupMiddleware → Validate session             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Query/Update
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE (PostgreSQL)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  store_category                                           │   │
│  │  ├─ id (PK)                                              │   │
│  │  ├─ name (CharField)                                     │   │
│  │  └─ slug (SlugField, unique)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  store_product                                            │   │
│  │  ├─ id (PK)                                              │   │
│  │  ├─ category_id (FK → store_category)                    │   │
│  │  ├─ name (CharField)                                     │   │
│  │  ├─ slug (SlugField, unique)                             │   │
│  │  ├─ description (TextField)                              │   │
│  │  ├─ price (DecimalField)                                 │   │
│  │  ├─ stock (PositiveIntegerField)                         │   │
│  │  ├─ image (ImageField)                                   │   │
│  │  ├─ is_available (BooleanField)                          │   │
│  │  ├─ camera_type, resolution_mp, ...specs                │   │
│  │  └─ created_at, updated_at (DateTimeField)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Django Sessions (for cart data)                         │   │
│  │  └─ cart: {"product_id": quantity, ...}                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### 1. Browse Products
```
User visits store
    ↓
Django loads categories via context_processors.py
    ↓
product_list() view queries DB
    ↓
Returns template with product list
    ↓
User sees Shop dropdown with all categories
```

### 2. Add to Cart
```
User clicks "Add to Cart" button
    ↓
JavaScript submits form to add_to_cart() endpoint
    ↓
View retrieves cart from request.session
    ↓
Updates: session['cart']['product_id'] = qty + 1
    ↓
Returns JSON with cart_count
    ↓
JavaScript updates cart badge display
```

### 3. Comparison
```
User clicks "Compare" on products
    ↓
JavaScript stores product in localStorage (ets_compare_v1)
    ↓
User visits compare page (store/compare.html)
    ↓
JavaScript fetches stored products
    ↓
For each product, calls /api/product/<id>/quick-view/
    ↓
Backend returns JSON with product details + category
    ↓
JavaScript validates: all same category?
    ↓
If yes: Display comparison table
If no: Show error message
```

### 4. Admin Management
```
Admin logs in to /admin/
    ↓
Django admin interface (store/admin.py)
    ↓
Can add/edit/delete Categories & Products
    ↓
Products are saved to database
    ↓
Frontend immediately shows updated data
```

---

## Component Interaction

```
┌─────────────────────┐         ┌─────────────────────┐
│   Views             │         │  Context Processors │
├─────────────────────┤         ├─────────────────────┤
│ product_list()      │◄────────►│ cart_count()        │
│ product_detail()    │         │ categories()        │
│ add_to_cart()       │         └─────────────────────┘
│ cart_view()         │
│ compare_page()      │         ┌─────────────────────┐
│ quick_view_...()    │         │  Models             │
└──────────┬──────────┘         ├─────────────────────┤
           │                    │ Category            │
           │                    │ Product             │
           │◄───────────────────┤ OrderItem           │
           │                    └─────────────────────┘
           │
           │                   ┌─────────────────────┐
           │                   │ Middleware          │
           └──────────────────►├─────────────────────┤
                               │ CartCleanupMiddle.  │
                               └─────────────────────┘
```

---

## Database Relationships

```
Category (1) ────────────────┬─────────────── (Many) Product
                             │
                             ├─ Product.category_id (FK)
                             │
                             └─ Product.objects.filter(category=cat)

Product (1) ──────────────────┬─────────────── (Many) OrderItem
                              │
                              ├─ OrderItem.product_id (FK)
                              │
                              └─ Product.objects.filter(orderitem__order=...)
```

---

## Session Data Structure

```
request.session = {
    'cart': {
        '2': 1,      # Product ID 2, quantity 1
        '5': 2,      # Product ID 5, quantity 2
        '10': 1      # Product ID 10, quantity 1
    },
    '_auth_user_id': '1',
    '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
    'sessionid': 'abc123...'
}
```

---

## Compare Feature Logic

```
┌─ User clicks Compare button
│
├─ JavaScript: extractProduct(button)
│  │
│  └─→ Get: id, name, price, url, image, category
│
├─ JavaScript: toggleCollection('compare', product)
│  │
│  └─→ Check: Is product.category same as existing items?
│      ├─ YES: Add to compare list
│      └─ NO: Show error, don't add
│
├─ User visits /compare/
│  │
│  ├─→ Fetch stored items from localStorage
│  │
│  ├─→ For each item: fetch /api/product/<id>/quick-view/
│  │
│  ├─→ Validate: All items same category?
│  │   ├─ YES: Render comparison table
│  │   └─ NO: Show error message
│  │
│  └─→ Display comparison with highlights
│      ├─ Best price (✓)
│      ├─ Best stock (✓)
│      ├─ Highest spec (✓)
│      └─ Side-by-side comparison
```

---

## Admin Dashboard Structure

```
/admin/
├─ Dashboard (index)
│
├─ Authentication
│  ├─ Users
│  ├─ Groups
│  └─ Permissions
│
├─ Store
│  ├─ Categories
│  │  ├─ Add Category
│  │  ├─ Edit Category
│  │  ├─ Delete Category
│  │  └─ List (shows product count)
│  │
│  └─ Products
│     ├─ Add Product
│     ├─ Edit Product
│     ├─ Delete Product
│     ├─ Filter by category
│     └─ Search by name/description
│
└─ Orders
   ├─ Orders
   └─ Order Items
```

---

## File Organization

```
static/
├─ css/
│  └─ site.css          ← All styling (including dropdown)
│
└─ js/
   └─ site.js           ← All frontend logic
                        ├─ Cart management
                        ├─ Compare feature
                        ├─ Wishlist
                        └─ Interactions

templates/
├─ base.html            ← Main layout with navbar
│
├─ home.html
│
└─ store/
   ├─ product_list.html
   ├─ product_detail.html
   ├─ compare.html
   ├─ cart.html
   └─ checkout.html

store/
├─ models.py            ← Category, Product models
├─ views.py             ← All view functions
├─ urls.py              ← URL routing
├─ admin.py             ← Admin customization
├─ context_processors.py ← cart_count, categories
│
├─ migrations/
│  └─ 0003_add_service_categories.py
│
└─ management/
   └─ commands/
      └─ add_sample_products.py
```

---

## Request/Response Flow

```
HTTP GET /category/dome-cameras/
    ↓
Django URL Router: urls.py
    ↓
Match: path('category/<slug:category_slug>/', views.product_list)
    ↓
Call: product_list(request, category_slug='dome-cameras')
    ↓
View Logic:
    ├─ Get category object
    ├─ Query products filtered by category
    ├─ Apply filters/sorting
    └─ Build context
        ├─ products (from views.py)
        ├─ category (from views.py)
        ├─ cart_count (from context_processors.py)
        └─ categories (from context_processors.py)
    ↓
Render: 'store/product_list.html' with context
    ↓
Template Rendering:
    ├─ Load static files
    ├─ Render base.html
    ├─ Render Shop dropdown with all categories
    ├─ Render product list
    └─ Render cart count in badge
    ↓
HTTP 200 response with HTML
    ↓
Browser displays page
```

---

## Technology Stack

```
Frontend:
├─ HTML5
├─ CSS3 (with CSS Grid, Flexbox)
├─ JavaScript (Vanilla)
├─ Bootstrap 5 (Framework)
└─ Bootstrap Icons

Backend:
├─ Python 3.12
├─ Django 6.0
└─ PostgreSQL (Database)

Architecture:
├─ MTV (Model-Template-View)
├─ Session-based state
├─ Middleware for data cleanup
└─ Context processors for template data
```

---

## Performance Optimization

```
Database:
├─ select_related() for categories
├─ Indexes on frequently queried fields
└─ Caching of category list

Frontend:
├─ CSS Minification
├─ JavaScript optimization
├─ Image lazy loading
└─ Bootstrap CDN

Server:
├─ GZIP compression
├─ Static file caching
├─ Session cleanup middleware
└─ Query optimization
```

---

**Architecture Documentation**
Built with ❤️ using Django + Bootstrap

This system is designed to be:
- **Scalable**: Easy to add more products/categories
- **Maintainable**: Clean code organization
- **Secure**: CSRF protection, session validation
- **Fast**: Optimized queries and caching
- **Professional**: Enterprise-grade eCommerce features
