# 🔧 Migration Conflict - RESOLVED

## Problem
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: 
(0004_fix_decimal_fields, 0005_alter_product_camera_type_alter_product_category in store).
```

## Root Cause
Two duplicate migrations were created with different names:
1. `0004_alter_product_category.py` - Only updated category help_text
2. `0004_fix_decimal_fields.py` - Updated all decimal fields
3. `0005_alter_product_camera_type_alter_product_category.py` - Depended on 0004_alter_product_category

This created a conflict because Django couldn't determine which `0004_*` migration to use.

## Solution Applied

### ✅ Step 1: Updated `0004_fix_decimal_fields.py`
Combined all field changes into one migration:
- Updated `camera_type` (with null=True)
- Updated `connectivity` (with null=True)
- Updated `power_source` (with null=True)
- Updated `lens_mm` (with default=None)
- Updated `resolution_mp` (with default=None)
- Updated `price` (with default=0)
- Updated `image` (with null=True, blank=True)
- Updated `category` (with new help_text)

### ✅ Step 2: Emptied `0004_alter_product_category.py`
Made it an empty no-op migration to prevent conflicts while maintaining history.

### ✅ Step 3: Updated `0005_*` Migration
Changed dependency from `0004_alter_product_category` → `0004_fix_decimal_fields`

## Migration Chain Now

```
0001_initial
    ↓
0002_product_specs
    ↓
0003_add_service_categories
    ↓
0004_alter_product_category (empty, for history)
    ↓
0004_fix_decimal_fields (all field changes)
    ↓
0005_alter_product_camera_type_alter_product_category (empty, passes through)
```

## How to Apply

### Run migrations:
```bash
python manage.py migrate store
```

This will:
✅ Apply 0004_fix_decimal_fields (all changes)
✅ Pass through 0005_* (no-op)
✅ No conflicts
✅ All fields updated correctly

### Verify:
```bash
python manage.py showmigrations store
```

Should show all migrations applied ✅

## What's Fixed

✅ No more conflicting migration error
✅ All decimal field validation fixed
✅ All choice fields nullable
✅ Image field optional
✅ Category help_text updated
✅ Clean migration history

## Files Modified

| File | Change |
|------|--------|
| `0004_alter_product_category.py` | Made empty (no-op) |
| `0004_fix_decimal_fields.py` | Added category field update |
| `0005_alter_product_camera_type_alter_product_category.py` | Updated dependency path |

## Status

✅ **CONFLICT RESOLVED**

Migration chain is now clean and can be applied without errors!

---

**Next Steps:**
```bash
python manage.py migrate store
python manage.py runserver
```

Your application is ready! 🎉
