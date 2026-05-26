# ✅ Models Updated - Adding Products via Admin Panel

## What Was Updated

### 1. ✅ Product Model (models.py)
Updated `CAMERA_TYPE_CHOICES` to include new camera types:
- Bullet
- Dome
- Turret ← NEW
- PTZ
- Wireless / WiFi ← NEW
- Fisheye ← NEW
- Indoor Cube

### 2. ✅ Admin Interface (admin.py)
Enhanced ProductAdmin with:
- Better field organization with descriptions
- Collapsible technical specs section
- Read-only timestamps
- Improved visual hierarchy
- Better help text

---

## How Categories Work

### ✅ Category System
All 13 categories are automatically available via ForeignKey:

**CCTV Cameras (6 types)**
- Dome Cameras
- Bullet Cameras
- PTZ Cameras
- Turret Cameras ← NEW
- Wireless / WiFi Cameras ← NEW
- Fisheye Cameras ← NEW

**Recording Devices (2 types)**
- DVR Systems
- NVR Systems

**Access Control (2 types)**
- Smart Locks
- Biometric Devices

**Automation & Other (2 types)**
- Home/Gate Automation
- Other Security Products

**Services (1 type)**
- CCTV Installations

---

## Step-by-Step: Add Product via Admin

### 1. Login to Admin
```
URL: http://localhost:8000/admin/
Username: (your superuser)
Password: (your password)
```

### 2. Click "Products" → "Add Product +"

### 3. Fill in Basic Information

**Category** (Select from dropdown)
- Choose from 13 available categories
- New categories available: Turret, Wireless/WiFi, Fisheye

**Name**
- Product name (e.g., "Hikvision Turret 2MP")
- Slug will auto-generate

**Description**
- Detailed product description
- Can include HTML

**Image**
- Upload product image
- Will be stored in `/media/products/`

**Is Available**
- Check to make product visible on store

### 4. Fill in Camera Technical Specs (Optional)

**Camera Type** (Select from dropdown)
- Bullet
- Dome
- Turret ← NEW
- PTZ
- Wireless / WiFi ← NEW
- Fisheye ← NEW
- Indoor Cube

**Resolution (MP)**
- Example: 2, 4, 5, 8

**Lens (MM)**
- Example: 2.8, 3.6, 4

**Field of View (Degrees)**
- Example: 90, 110, 120

**Night Vision Range (Meters)**
- Example: 30, 50, 100

**Frame Rate (FPS)**
- Example: 25, 30

**Weatherproof Rating**
- Example: IP66, IP67

**Connectivity**
- Wired
- Wi-Fi
- Hybrid

**Power Source**
- PoE
- DC 12V
- Battery
- Solar

**Storage Support**
- Example: NVR, microSD, Cloud

**Audio Support**
- Check if supported

**AI Detection**
- Check if supported

**Warranty (Years)**
- Number of warranty years

### 5. Fill in Pricing & Inventory

**Price (Rupees)**
- Product price in ₹
- Example: 4500, 8999

**Stock**
- Available quantity
- Example: 10, 15, 20

### 6. Click "Save"

✅ Product is now visible on store!

---

## Example: Add Turret Camera

```
Category: Turret Cameras
Name: Hikvision Turret 2MP
Description: Professional 2MP turret camera with night vision...
Image: (upload image)
Is Available: ✓

Camera Type: Turret
Resolution: 2.0 MP
Lens: 3.6 MM
FOV: 90 degrees
Night Vision: 30 meters
Frame Rate: 25 fps
Weatherproof: IP67
Connectivity: Wired
Power Source: PoE
Storage: NVR, microSD
Audio Support: ✓
AI Detection: ✓
Warranty: 2 years

Price: 4500
Stock: 15
```

Then click **Save** → Product appears on store!

---

## Example: Add WiFi Camera

```
Category: Wireless / WiFi Cameras
Name: 4MP WiFi Camera Pro
Description: Advanced 4MP wireless camera with cloud storage...
Image: (upload image)
Is Available: ✓

Camera Type: Wireless / WiFi
Resolution: 4.0 MP
Lens: 2.8 MM
FOV: 110 degrees
Night Vision: 40 meters
Frame Rate: 30 fps
Weatherproof: IP66
Connectivity: Wi-Fi
Power Source: Battery
Storage: Cloud, microSD
Audio Support: ✓
AI Detection: ✓
Warranty: 2 years

Price: 6800
Stock: 12
```

Then click **Save** → Product appears on store!

---

## Admin Features

### ✅ List View
- See all products
- Filter by category, availability, specs
- Search by name/description
- Bulk actions

### ✅ Edit View
- Update any field
- Add/remove image
- Change category
- Update pricing

### ✅ Search
- Search by product name
- Search by description
- Search by specs

### ✅ Filters
- Filter by category ← All 13 categories available
- Filter by camera type ← Updated with new types
- Filter by availability
- Filter by connectivity
- Filter by AI detection
- Filter by audio support

### ✅ Display
- Shows product count per category
- Shows creation date
- Shows last update
- Shows availability status

---

## Quick Tips

### ✅ Auto-Generate Slug
- Enter product name
- Slug auto-generates
- Can be edited if needed

### ✅ Optional Fields
- Camera specs are optional
- For non-camera products, leave blank
- For example: Installation services

### ✅ Price Format
- Enter as number: 4500 (not ₹4500)
- Decimal support: 4500.00
- System handles formatting

### ✅ Stock Management
- 0 = Out of Stock (product still shows but not purchasable)
- > 0 = In Stock (can be purchased)
- System prevents over-ordering

### ✅ Image Upload
- Supported: JPG, PNG, WebP
- Max size: ~5MB recommended
- Will be resized/optimized

---

## Troubleshooting

### Categories Not Showing?
```bash
python manage.py migrate store
python manage.py runserver
```
Then refresh admin page.

### Camera Type Missing?
- Restart server
- Clear browser cache
- Try again

### Product Not Appearing on Store?
- Check "Is Available" is checked
- Check category is correct
- Check stock > 0 (optional)
- Refresh frontend

### Image Not Uploading?
- Check file format (JPG, PNG, WebP)
- Check file size < 5MB
- Check media folder permissions
- Try different image

---

## API Integration

When you add products via admin, they're available for:

✅ Product Listing (`/` or `/category/...`)
✅ Product Detail (`/product/...`)
✅ Quick View API (`/api/product/...`)
✅ Search & Filter
✅ Comparison (same category only)
✅ Cart (add to cart)

---

## Database Structure

```
Category Table
├── id (PK)
├── name (unique)
└── slug (unique)

Product Table
├── id (PK)
├── category_id (FK → Category)
├── name (unique)
├── slug (unique)
├── description
├── camera_type (choices)
├── resolution_mp
├── lens_mm
├── field_of_view_deg
├── night_vision_range_m
├── frame_rate_fps
├── weatherproof_rating
├── connectivity (choices)
├── power_source (choices)
├── storage_support
├── audio_support
├── ai_detection
├── warranty_years
├── price
├── stock
├── image
├── is_available
├── created_at
└── updated_at
```

---

## Next Steps

1. ✅ Models updated
2. ✅ Admin interface enhanced
3. 👉 **Add products via admin panel**
4. View on frontend
5. Test comparison & cart

---

## Commands Reference

```bash
# View all products in shell
python manage.py shell
>>> from store.models import Product, Category
>>> Product.objects.all()
>>> Category.objects.all()

# Count products per category
>>> from django.db.models import Count
>>> Category.objects.annotate(count=Count('products'))

# Export products
# (will need to add Django Suit or similar)
```

---

## Product Examples to Add

### Turret Cameras
- Hikvision Turret 2MP
- Dahua 4MP Turret
- CP Plus 5MP Turret

### Wireless / WiFi Cameras
- 4MP WiFi Camera Pro
- 2MP Battery WiFi Camera
- Solar WiFi Camera

### Fisheye Cameras
- 360° Fisheye 5MP
- 180° Panoramic Camera
- Compact Fisheye 2MP

---

## Status

✅ **Models Updated**
✅ **Admin Enhanced**
✅ **13 Categories Available**
✅ **6 Camera Types Available**
✅ **Ready to Add Products**

---

Start adding products now! 🎯

Go to: http://localhost:8000/admin/store/product/add/
