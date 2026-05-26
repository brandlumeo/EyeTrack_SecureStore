# CCTV Specifications Fields Implementation

## Project Overview

**Objective**: Extend the Product model to include CCTV camera specification fields and integrate them with the Django admin panel and compare page.

**Status**: ✅ COMPLETE  
**Date**: March 10, 2026

---

## Changes Made

### 1. Extended Product Model

Added the following CCTV specification fields directly to the `Product` model:

#### Text Fields (CharField)
- **camera_type**: Type of CCTV camera (bullet, dome, turret, PTZ, wireless, fisheye, cube)
- **resolution**: Resolution specification (e.g., 4K, 2MP, 5MP)
- **night_vision_range**: Night vision range in meters (e.g., 30m)
- **field_of_view**: Field of view in degrees (e.g., 90°)
- **lens**: Lens specification (e.g., 3.6mm)
- **frame_rate**: Frame rate (e.g., 30fps)
- **weatherproof**: Weatherproof rating (e.g., IP66)
- **connectivity**: Connectivity type (wired, Wi-Fi, hybrid)
- **power_source**: Power source type (PoE, DC 12V, battery, solar)
- **storage_support**: Storage options (NVR, microSD, Cloud)
- **warranty**: Warranty period (e.g., 2 years)

#### Boolean Fields
- **audio_support**: Whether the camera supports audio
- **ai_detection**: Whether the camera has AI detection

### 2. Updated Django Admin Panel

**File**: `store/admin.py`

**Changes**:
- Added new fieldset **"📷 CCTV Specifications"** to the ProductAdmin
- Organized all specification fields in a collapsible section
- Easy to expand/collapse with class `collapse`

**Fieldset Structure**:
```python
('📷 CCTV Specifications', {
    'fields': (
        'camera_type', 'resolution', 'night_vision_range', 
        'field_of_view', 'lens', 'frame_rate', 'weatherproof',
        'connectivity', 'power_source', 'storage_support',
        'audio_support', 'ai_detection', 'warranty'
    ),
    'description': 'CCTV camera technical specifications',
    'classes': ('collapse',)
})
```

### 3. Updated Product Specification Builder

**File**: `store/views.py` - `_build_product_specs()` function

**Changes**:
- Now checks Product model fields FIRST for specifications
- Falls back to related CameraSpecification object for backward compatibility
- Returns specifications with keys matching what the compare page expects:
  - `camera_type`
  - `resolution_mp`
  - `night_vision_range_m`
  - `field_of_view_deg`
  - `lens`
  - `frame_rate`
  - `weatherproof`
  - `connectivity`
  - `power_source`
  - `storage_support`
  - `audio_support`
  - `ai_detection`
  - `warranty_years`

### 4. Created Migration

**File**: `store/migrations/0010_add_cctv_specifications.py`

**Adds**:
- 13 new fields to the Product model
- All fields are optional (blank=True) for backward compatibility
- BooleanFields default to False
- CharField fields have appropriate choices where applicable

---

## How to Use

### Adding CCTV Product in Admin

1. Go to Django Admin → Store → Products
2. Click "Add Product"
3. Fill in basic information (category, name, description, etc.)
4. Scroll to **"📷 CCTV Specifications"** section
5. Click to expand the section
6. Fill in any relevant specifications:
   - Camera Type: Select from dropdown (Bullet, Dome, Turret, PTZ, etc.)
   - Resolution: Enter text (e.g., "4K" or "2MP")
   - Night Vision Range: Enter text (e.g., "30m")
   - Field of View: Enter text (e.g., "90°")
   - Lens: Enter text (e.g., "3.6mm")
   - Frame Rate: Enter text (e.g., "30fps")
   - Weatherproof: Enter text (e.g., "IP66")
   - Connectivity: Select from dropdown (Wired, Wi-Fi, Hybrid)
   - Power Source: Select from dropdown (PoE, DC 12V, Battery, Solar)
   - Storage Support: Enter text (e.g., "NVR, microSD, Cloud")
   - Audio Support: Check if supported
   - AI Detection: Check if supported
   - Warranty: Enter text (e.g., "2 years")

7. Click "Save" to create the product

### Compare Page Integration

The compare page automatically uses these specifications:
- When viewing the compare page, products with specifications will show their details
- The compare logic in `site.js` looks for these spec keys in the product data
- Specifications are now returned directly from the Product model

### API Response

When the quick-view API endpoint is called (`/api/product/<id>/quick-view/`), it returns:

```json
{
    "ok": true,
    "product": {
        "id": 1,
        "name": "Hikvision 8MP Camera",
        "price": "45000",
        "stock": 10,
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
}
```

---

## Migration Instructions

### Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

The migration file `0010_add_cctv_specifications.py` will:
1. Add 13 new fields to the Product table
2. Set default values for BooleanFields (False)
3. Leave CharField fields empty initially (can be filled per product)

### No Data Loss

- All existing products are preserved
- New fields are optional, so no validation errors
- Existing products won't show specs until manually filled in

---

## Model Field Reference

```python
class Product(models.Model):
    # ... existing fields ...
    
    # CCTV Specifications
    camera_type = CharField(choices=[...], blank=True, null=True)
    resolution = CharField(blank=True)
    night_vision_range = CharField(blank=True)
    field_of_view = CharField(blank=True)
    lens = CharField(blank=True)
    frame_rate = CharField(blank=True)
    weatherproof = CharField(blank=True)
    connectivity = CharField(choices=[...], blank=True, null=True)
    power_source = CharField(choices=[...], blank=True, null=True)
    storage_support = CharField(blank=True)
    audio_support = BooleanField(default=False)
    ai_detection = BooleanField(default=False)
    warranty = CharField(blank=True)
```

---

## Backward Compatibility

The implementation maintains full backward compatibility:
- Existing CameraSpecification model still works
- `_build_product_specs()` checks Product fields FIRST, then falls back to CameraSpecification
- Existing products using the old system continue to work
- New products can use the simpler Product model fields

---

## Benefits

1. **Simpler Data Entry**: No need to create separate CameraSpecification objects
2. **Direct Access**: Specifications are on the Product object itself
3. **API Simplicity**: No need for select_related() in queries
4. **Compare Page**: Specifications automatically display correctly
5. **Admin UX**: Clean, organized fieldset for easy management
6. **Optional Fields**: Don't need to fill in all specs if not applicable

---

## Testing Checklist

- [x] All fields added to Product model
- [x] Admin panel shows new fieldset
- [x] Fieldset is collapsible
- [x] Migration created correctly
- [x] API endpoint returns specifications
- [x] Compare page accesses specifications
- [x] Backward compatibility maintained
- [x] No existing data affected

---

## Files Modified

| File | Changes |
|------|---------|
| `store/models.py` | Added 13 specification fields to Product model |
| `store/admin.py` | Added CCTV Specifications fieldset |
| `store/views.py` | Updated `_build_product_specs()` function |
| `store/migrations/0010_add_cctv_specifications.py` | New migration file |

---

## Example Product Data

After implementation, a complete CCTV camera product might look like:

```
Product: Hikvision DS-2CD2T43G0-I8
Category: CCTV Cameras
Price: ₹45,000
Stock: 10

CCTV Specifications:
- Camera Type: Bullet
- Resolution: 4MP
- Night Vision Range: 30m
- Field of View: 90°
- Lens: 3.6mm
- Frame Rate: 25fps
- Weatherproof: IP67
- Connectivity: Wired
- Power Source: PoE
- Storage Support: NVR, microSD
- Audio Support: ✓ Yes
- AI Detection: ✓ Yes
- Warranty: 2 years
```

---

## Next Steps (Optional)

For further enhancement, consider:
1. Add image gallery support for products
2. Add product comparison charts
3. Add PDF export for specifications
4. Add product reviews and ratings
5. Add product variants/models

---

## Version History

**v1.0 - Initial CCTV Specifications Implementation**
- Added 13 specification fields to Product model
- Updated Django admin with organized fieldset
- Enhanced specification builder function
- Created migration
- Date: March 10, 2026

