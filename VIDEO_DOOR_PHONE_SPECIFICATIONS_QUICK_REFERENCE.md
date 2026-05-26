# Video Door Phone Specifications - Quick Reference Guide

## Overview

Video Door Phone (VDP) specifications have been added to the Product model. These fields appear in Django admin for products categorized as "Video Door Phones" and display on product detail and compare pages.

---

## Model Fields Added

### Text Fields (Freeform Input)

- **screen_size**: Screen size (e.g., "7 inch", "10.1 inch")
- **camera_resolution**: Camera resolution (e.g., "2MP", "5MP")
- **storage_support_vdp**: Storage options (e.g., "microSD, Cloud, Local")
- **warranty_vdp**: Warranty period (e.g., "1 year", "2 years")

### Choice Fields (Dropdowns)

**connectivity_type**:
- Wired
- Wireless
- Wi-Fi
- Hybrid

**unlock_method**:
- RFID Card
- PIN Code
- Fingerprint
- Mobile App
- Mechanical Key
- Multiple Methods

**power_source_vdp**:
- PoE
- DC 12V
- Battery
- Hybrid

**installation_type**:
- Surface Mount
- Flush Mount
- Both

### Boolean Fields (Checkboxes)

- **night_vision**: Has night vision capability
- **audio_communication**: Supports audio communication
- **mobile_app_support**: Supports mobile app control

---

## Django Admin Usage

### Location
Admin Panel → Store → Products → [Edit Product]

### When It Appears
- Only shows for products where Category = "Video Door Phones"
- For CCTV Cameras, shows CCTV Specifications instead
- For other categories, no specifications section

### Layout
```
📦 Basic Information
💰 Inventory & Pricing
📞 Video Door Phone Specifications (NEW - collapsible)
  ├─ Screen Size
  ├─ Camera Resolution
  ├─ Night Vision (checkbox)
  ├─ Connectivity Type (dropdown)
  ├─ Unlock Method (dropdown)
  ├─ Audio Communication (checkbox)
  ├─ Mobile App Support (checkbox)
  ├─ Storage Support
  ├─ Power Source (dropdown)
  ├─ Installation Type (dropdown)
  └─ Warranty
```

### How to Fill

1. Set product category to "Video Door Phones"
2. Expand "📞 Video Door Phone Specifications"
3. Fill text fields with specifications
4. Select from dropdowns for choice fields
5. Check checkboxes for boolean features
6. Save product

---

## Example Product Data

### Basic Video Door Phone

```
Screen Size: 7 inch
Camera Resolution: 2MP
Night Vision: ✓
Connectivity Type: Wired
Unlock Method: RFID Card
Audio Communication: ✓
Mobile App Support: ✗
Storage Support: microSD
Power Source: PoE
Installation Type: Surface Mount
Warranty: 1 year
```

### Smart Video Door Phone

```
Screen Size: 10.1 inch
Camera Resolution: 5MP
Night Vision: ✓
Connectivity Type: Wi-Fi
Unlock Method: Mobile App
Audio Communication: ✓
Mobile App Support: ✓
Storage Support: microSD, Cloud, Local
Power Source: Hybrid
Installation Type: Both
Warranty: 2 years
```

---

## Compare Page Integration

### How It Works

1. Add Video Door Phone products to compare
2. Compare page detects category as "Video Door Phones"
3. Shows Video Door Phone specification rows
4. Highlights best values (where applicable)
5. Displays Yes/No with checkmarks

### Specifications Shown

- Screen Size
- Camera Resolution
- Night Vision (✓/✗)
- Connectivity Type
- Unlock Method
- Audio Communication (✓/✗)
- Mobile App Support (✓/✗)
- Storage Support
- Power Source
- Installation Type
- Warranty

---

## Product Detail Page

### Automatic Display

- Specifications tab shows all filled VDP specs
- Empty fields are automatically hidden
- Uses same data source as compare page
- No template changes needed

### Example Display

```
Screen Size: 7 inch
Camera Resolution: 2MP
Night Vision: Yes
Connectivity Type: Wi-Fi
Unlock Method: Mobile App
Audio Communication: Yes
Mobile App Support: Yes
Storage Support: microSD, Cloud
Power Source: PoE
Installation Type: Surface Mount
Warranty: 2 years
```

---

## API Response

Product quick-view API returns:

```json
{
    "specs": {
        "screen_size": "7 inch",
        "camera_resolution": "2MP",
        "night_vision": "Yes",
        "connectivity_type": "Wi-Fi",
        "unlock_method": "Mobile App",
        "audio_communication": "Yes",
        "mobile_app_support": "Yes",
        "storage_support": "microSD, Cloud",
        "power_source": "PoE",
        "installation_type": "Surface Mount",
        "warranty": "2 years"
    }
}
```

---

## Important Notes

### Category Requirement
- Specifications only appear for "Video Door Phones" category
- Make sure category exists and is spelled correctly
- Case-sensitive: "Video Door Phones" (not "video door phones")

### Field Naming
- Some fields have "_vdp" suffix to avoid conflicts:
  - `storage_support_vdp` (not `storage_support`)
  - `power_source_vdp` (not `power_source`)
  - `warranty_vdp` (not `warranty`)

### Optional Fields
- All fields are optional
- Leave blank if specification doesn't apply
- Boolean fields default appropriately

---

## Troubleshooting

### Specs not showing in admin

1. Check product category is exactly "Video Door Phones"
2. Refresh browser (clear cache)
3. Verify migration was applied

### Specs not showing on compare page

1. Ensure all compared products are Video Door Phones
2. Check that specs are filled in admin
3. Verify API returns specs data

### Wrong specs showing

1. Compare page shows specs based on first product's category
2. All products must be from same category
3. Mixed categories show error message

---

## Migration Required

**Important**: Run this command before using:

```bash
python manage.py migrate
```

This creates the 11 new database columns for VDP specifications.

---

## Files Changed

- `store/models.py` - Added 11 fields
- `store/admin.py` - Added fieldset and dynamic logic
- `store/views.py` - Updated spec builder
- `static/js/site.js` - Dynamic compare specs
- `store/migrations/0011_add_video_door_phone_specifications.py` - Migration

---

## Backward Compatibility

✅ **Fully compatible**:
- Existing CCTV products unchanged
- Existing functionality preserved
- Can mix old and new data
- No breaking changes

---

## Quick Start

1. **Apply migration**: `python manage.py migrate`
2. **Create category**: "Video Door Phones" (if not exists)
3. **Add product**: Set category to "Video Door Phones"
4. **Fill specs**: Expand VDP Specifications section
5. **Save**: Specifications now available everywhere
6. **Test**: View on detail page and compare page

---

## Version

**v1.0** - March 10, 2026

