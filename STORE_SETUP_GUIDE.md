# EyeTrack Solutions - Store Setup Guide

## ✅ Completed Setup

### 1. Professional Category Structure

Your store now has 10 professional security product and service categories:

**CCTV Cameras**
- Dome Cameras
- Bullet Cameras  
- PTZ Cameras

**Recording Devices**
- DVR Systems
- NVR Systems

**Access Control**
- Smart Locks
- Biometric Devices

**Automation & Other**
- Home/Gate Automation
- Other Security Products

**Services**
- CCTV Installations

---

## 🚀 How to Use

### Step 1: Apply Database Migrations

Run the migration to create all categories:

```bash
python manage.py migrate store
```

### Step 2: Add Sample Products

Add sample products to all categories:

```bash
python manage.py add_sample_products
```

This will add 13 sample products including:
- 2 Dome Cameras (Hikvision 2MP, Dahua 4MP)
- 2 Bullet Cameras (CP Plus 5MP, Hikvision 8MP)
- 1 PTZ Camera (Hikvision 20x Zoom)
- 2 DVR Systems (8-channel, 16-channel)
- 2 NVR Systems (8-channel, 32-channel Enterprise)
- 1 Smart Lock
- 1 Biometric Device
- 1 Gate Automation
- 2 Installation Services

### Step 3: Start Your Server

```bash
python manage.py runserver
```

Navigate to: `http://localhost:8000`

---

## 📋 Sample Products Reference

### Camera Products

| Product | Category | Price | Resolution |
|---------|----------|-------|-----------|
| Hikvision Dome 2MP | Dome Cameras | ₹4,500 | 2MP |
| Dahua 4MP Smart Dome | Dome Cameras | ₹6,800 | 4MP |
| CP Plus 5MP Bullet | Bullet Cameras | ₹5,200 | 5MP |
| Hikvision 8MP Bullet Pro | Bullet Cameras | ₹8,500 | 8MP |
| Hikvision PTZ 2MP | PTZ Cameras | ₹12,000 | 2MP |

### Recording Devices

| Product | Category | Price | Channels |
|---------|----------|-------|----------|
| 8 Channel DVR System | DVR Systems | ₹8,999 | 8 |
| 16 Channel DVR Pro | DVR Systems | ₹15,999 | 16 |
| 8 Channel NVR System | NVR Systems | ₹12,500 | 8 |
| 32 Channel NVR Enterprise | NVR Systems | ₹45,000 | 32 |

### Access Control

| Product | Category | Price |
|---------|----------|-------|
| Smart Door Lock Pro | Smart Locks | ₹4,500 |
| Fingerprint Time Attendance | Biometric Devices | ₹8,500 |

### Services

| Product | Category | Price |
|---------|----------|-------|
| CCTV Installation (2-4 Cameras) | CCTV Installations | ₹5,000 |
| Complete CCTV Solution (8+ Cameras) | CCTV Installations | ₹25,000 |

---

## 🔄 Product Comparison Feature

Your store has an intelligent comparison system:

✅ **Same Category Comparison**: Users can only compare products from the same category
- Dome Cameras vs Dome Cameras ✓
- Bullet Cameras vs Bullet Cameras ✓
- DVR vs DVR ✓
- Smart Lock vs Biometric ✗ (Different categories)

✅ **Maximum 4 Products**: Users can compare up to 4 products at a time

✅ **Live Data**: Comparison updates with real product data

---

## 🎨 Frontend Enhancements

### Navigation Menu

The "Shop" dropdown now shows:
- All Products (grid view)
- Organized category groups
- Icons for each category type
- Responsive mobile design

### Admin Interface

Category management improved with:
- Product count display
- Better organization
- Easy to add/edit categories

---

## 📊 Next Steps

### To Add More Products:

1. Go to Django Admin: `http://localhost:8000/admin/`
2. Click "Products" → "Add Product"
3. Fill in details:
   - **Name**: Product name
   - **Category**: Select from 10 categories
   - **Price**: Product price in rupees
   - **Stock**: Available quantity
   - **Description**: Product details
   - **Image**: Upload product image
   - **Technical Specs** (if applicable):
     - Camera Type (Bullet, Dome, PTZ)
     - Resolution (MP)
     - Night Vision Range (meters)
     - Connectivity (Wired, WiFi)
     - Power Source (PoE, DC12V)
     - And more...

### To Edit Categories:

1. Go to Admin → Categories
2. Click category name to edit
3. Change name, description, etc.

---

## 🛠 Customization Guide

### Add New Category

```bash
# Edit store/migrations/0003_add_service_categories.py
# Add new dictionary to categories_data list:
{
    'name': 'Your Category Name',
    'slug': 'your-category-slug'
}

python manage.py migrate store
```

### Modify Sample Products

Edit `store/management/commands/add_sample_products.py`

Add new product to `products_data` list:

```python
{
    'name': 'Product Name',
    'category_slug': 'category-slug',
    'description': 'Product description',
    'price': Decimal('9999.00'),
    'stock': 10,
    'is_available': True,
}
```

Then run:
```bash
python manage.py add_sample_products
```

---

## 📱 Mobile Responsive

✅ All features are fully responsive:
- Category dropdown on mobile
- Product grid adapts to screen size
- Navigation collapses on small screens
- Touch-friendly buttons

---

## 🔒 Cart & Comparison Features

### Cart System
- Session-based cart management
- Real-time cart count updates
- Add/remove/update quantities
- Session cleanup middleware

### Comparison System
- Same-category only comparison
- Maximum 4 products
- Live product data fetch
- Best price & stock highlights
- Share comparison link
- Export to PDF

---

## 🎯 Store Features Summary

✅ **Professional Structure**: Organized categories
✅ **Product Management**: Easy admin interface
✅ **Comparison**: Smart same-category comparison
✅ **Mobile Ready**: Fully responsive design
✅ **Cart System**: Session-based, no database overhead
✅ **Admin Tools**: Category and product management
✅ **Sample Data**: 13 sample products ready

---

## ⚠️ Important Notes

1. **Database**: Uses PostgreSQL (configured in settings.py)
2. **Static Files**: CSS/JS in `/static/` directory
3. **Product Images**: Uploaded to `/media/products/`
4. **Admin Access**: `http://localhost:8000/admin/`
5. **Cart Data**: Stored in Django sessions (server-side)

---

## 🆘 Troubleshooting

**Categories not showing?**
```bash
python manage.py migrate store
```

**Products command not found?**
```bash
# Ensure file exists at:
# store/management/commands/add_sample_products.py
# With __init__.py files in:
# store/management/__init__.py
# store/management/commands/__init__.py
```

**Admin doesn't show categories?**
```bash
# Restart server:
python manage.py runserver
```

---

## 📞 Support

For adding more features or customizations, refer to:
- Django Admin Documentation
- Store app models: `store/models.py`
- Views: `store/views.py`
- Templates: `templates/store/`

---

**Status**: ✅ Ready for Development

Your EyeTrack Solutions store is now professionally structured and ready for products!
