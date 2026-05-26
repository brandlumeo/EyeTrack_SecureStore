# CCTV Specifications - Quick Reference Guide

## Overview

CCTV specification fields have been added directly to the Product model in Django. These fields automatically appear in the Django admin panel and are used by the compare page.

---

## Model Fields Added

### Choice Fields (Dropdowns)

**camera_type** (Choices):
- Bullet
- Dome
- Turret
- PTZ
- Wireless / WiFi
- Fisheye
- Indoor Cube

**connectivity** (Choices):
- Wired
- Wi-Fi
- Hybrid

**power_source** (Choices):
- PoE
- DC 12V
- Battery
- Solar

### Text Fields (Freeform Input)

- **resolution**: Resolution (e.g., "4K", "2MP", "5MP")
- **night_vision_range**: Night vision range (e.g., "30m", "50m")
- **field_of_view**: Field of view (e.g., "90°", "120°")
- **lens**: Lens specification (e.g., "3.6mm", "2.8mm-12mm")
- **frame_rate**: Frame rate (e.g., "30fps", "25fps")
- **weatherproof**: Weatherproof rating (e.g., "IP67", "IP66")
- **storage_support**: Storage options (e.g., "NVR, microSD, Cloud")
- **warranty**: Warranty period (e.g., "2 years", "3 years")

### Boolean Fields (Checkboxes)

- **audio_support**: Check if camera supports audio
- **ai_detection**: Check if camera has AI detection

---

## Django Admin Usage

### Location
Admin Panel → Store → Products → (Edit Product)

### Layout
1. **📦 Basic Information** - Product name, category, description
2. **💰 Inventory & Pricing** - Price, stock
3. **📷 CCTV Specifications** (Collapsible section)

### How to Fill In Specs

1. Click the "CCTV Specifications" section to expand
2. For choice fields (camera_type, connectivity, power_source), select from dropdown
3. For text fields, type in the specification value
4. For boolean fields, check the checkbox if applicable
5. Leave blank if specification is not applicable to this product
6. Click "Save" to update the product

---

## Data Entry Examples

### Example 1: Bullet Camera

```
Camera Type: Bullet
Resolution: 8MP
Night Vision Range: 30m
Field of View: 90°
Lens: 3.6mm
Frame Rate: 30fps
Weatherproof: IP67
Connectivity: Wired
Power Source: PoE
Storage Support: NVR, microSD
Audio Support: ✓
AI Detection: ✓
Warranty: 2 years
```

### Example 2: Dome Camera

```
Camera Type: Dome
Resolution: 4K
Night Vision Range: 20m
Field of View: 120°
Lens: 2.8mm-12mm
Frame Rate: 25fps
Weatherproof: IP65
Connectivity: Wi-Fi
Power Source: Battery
Storage Support: Cloud
Audio Support: ✗
AI Detection: ✗
Warranty: 1 year
```

### Example 3: PTZ Camera

```
Camera Type: PTZ
Resolution: 2MP
Night Vision Range: 50m
Field of View: Variable
Lens: 4.3mm-129mm
Frame Rate: 30fps
Weatherproof: IP67
Connectivity: Wired
Power Source: PoE
Storage Support: NVR
Audio Support: ✓
AI Detection: ✓
Warranty: 3 years
```

---

## Compare Page Integration

### How It Works

1. When products are added to compare, the API fetches their specifications
2. The specifications come from the Product model fields
3. Compare page displays them in a table format
4. Best values are highlighted (highest resolution, best price, etc.)

### What Shows on Compare Page

- Camera Type
- Resolution
- Night Vision Range
- Field of View
- Lens
- Frame Rate
- Weatherproof
- Connectivity
- Power Source
- Storage Support
- Audio Support (Yes/No)
- AI Detection (Yes/No)
- Warranty

---

## Database Fields

### SQL Column Names

```sql
product.camera_type          -- VARCHAR(20)
product.resolution           -- VARCHAR(50)
product.night_vision_range   -- VARCHAR(50)
product.field_of_view        -- VARCHAR(50)
product.lens                 -- VARCHAR(50)
product.frame_rate           -- VARCHAR(50)
product.weatherproof         -- VARCHAR(50)
product.connectivity         -- VARCHAR(20)
product.power_source         -- VARCHAR(20)
product.storage_support      -- VARCHAR(200)
product.audio_support        -- BOOLEAN
product.ai_detection         -- BOOLEAN
product.warranty             -- VARCHAR(50)
```

---

## API Response

When products are fetched for compare page:

```json
{
    "specs": {
        "camera_type": "Bullet",
        "resolution_mp": "8MP",
        "night_vision_range_m": "30m",
        "field_of_view_deg": "90°",
        "lens": "3.6mm",
        "frame_rate": "30fps",
        "weatherproof": "IP67",
        "connectivity": "Wired",
        "power_source": "PoE",
        "storage_support": "NVR, microSD",
        "audio_support": "Yes",
        "ai_detection": "Yes",
        "warranty_years": "2 years"
    }
}
```

---

## Important Notes

- **All fields are optional**: Leave blank if not applicable
- **Backward compatible**: Existing products using CameraSpecification model still work
- **Auto-populated in compare**: No additional setup needed
- **Direct on Product model**: No related object lookup required
- **Admin collapsible**: CCTV Specifications can be collapsed to reduce clutter

---

## Troubleshooting

### Specs not showing on compare page

1. Check if product has any specifications filled in admin
2. Refresh the page to clear cache
3. Verify API endpoint returns specs: `/api/product/<id>/quick-view/`

### Admin panel not showing CCTV Specifications section

1. Ensure migration was applied: `python manage.py migrate`
2. Refresh browser (clear cache)
3. Check that admin.py has the updated fieldsets

### Old specifications still showing

1. The system checks Product model fields FIRST
2. If you have both old CameraSpecification and new Product fields, Product fields take priority
3. To use old data, clear the new Product fields or migrate old data

---

## Files Modified

- `store/models.py` - Added 13 fields to Product model
- `store/admin.py` - Added CCTV Specifications fieldset
- `store/views.py` - Updated specification builder
- `store/migrations/0010_add_cctv_specifications.py` - Migration

---

## Version

**v1.0** - March 10, 2026

