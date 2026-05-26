# CCTV Specifications - Migration Error & Resolution

## Error Encountered

```
ProgrammingError at /
column store_product.camera_type does not exist
```

## Root Cause

The Product model was extended with new fields, but the migration hasn't been applied to the database yet. Django is trying to query these columns, but they don't exist in the database table.

## Quick Fix

### Step 1: Open Terminal/Command Prompt

Navigate to your project directory:
```bash
cd c:\Users\MUHAMMAD SHAMIL CV\PycharmProjects\EyeTrack_SecureStore
```

### Step 2: Apply the Migration

Run the migrate command:
```bash
python manage.py migrate
```

**Expected Output**:
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, orders, sessions, store

Running migrations:
  Applying store.0010_add_cctv_specifications... OK
```

### Step 3: Verify Success

After the migration completes successfully, refresh your browser:
```
http://127.0.0.1:8000/
```

The error should be gone and your site should work normally.

---

## What the Migration Does

The migration file `0010_add_cctv_specifications.py` adds these columns to the `store_product` table:

1. `camera_type` - VARCHAR(20)
2. `resolution` - VARCHAR(50)
3. `night_vision_range` - VARCHAR(50)
4. `field_of_view` - VARCHAR(50)
5. `lens` - VARCHAR(50)
6. `frame_rate` - VARCHAR(50)
7. `weatherproof` - VARCHAR(50)
8. `connectivity` - VARCHAR(20)
9. `power_source` - VARCHAR(20)
10. `storage_support` - VARCHAR(200)
11. `audio_support` - BOOLEAN (DEFAULT: false)
12. `ai_detection` - BOOLEAN (DEFAULT: false)
13. `warranty` - VARCHAR(50)

---

## Verification Steps

### Check if Migration was Applied

```bash
python manage.py showmigrations store
```

You should see:
```
store
 [X] 0001_initial
 [X] 0002_product_specs
 [X] 0003_add_service_categories
 ...
 [X] 0010_add_cctv_specifications
```

The `[X]` means it's been applied.

### Check Database Columns (Optional)

If using SQLite (default), you can inspect the database:

**Using Django shell**:
```bash
python manage.py shell
```

Then:
```python
from store.models import Product
from django.db import connection

# Get table info
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(store_product)")
    columns = cursor.fetchall()
    for col in columns:
        print(col[1])  # Column name
```

You should see all the new fields listed.

---

## If Migration Doesn't Work

### Issue: "No migrations to apply"

This means the migration file isn't being detected. Verify it exists:
```
store/migrations/0010_add_cctv_specifications.py
```

If missing, the migration file needs to be created (it should already exist).

### Issue: "Conflict between migrations"

If you get a conflict error, try:
```bash
python manage.py migrate --fake-initial
```

**WARNING**: Only use this if you're sure the database is in a consistent state.

### Issue: "Table already exists"

If the columns already exist in your database, mark the migration as applied:
```bash
python manage.py migrate --fake store 0010_add_cctv_specifications
```

---

## Complete Workflow

1. **Extended Product Model** ✓ (Done)
   - Added 13 new fields to `store/models.py`

2. **Updated Admin Panel** ✓ (Done)
   - Added CCTV Specifications fieldset to `store/admin.py`

3. **Updated Specification Builder** ✓ (Done)
   - Modified `_build_product_specs()` in `store/views.py`

4. **Created Migration** ✓ (Done)
   - Migration file: `store/migrations/0010_add_cctv_specifications.py`

5. **Apply Migration** ← YOU ARE HERE
   ```bash
   python manage.py migrate
   ```

6. **Add Product Specifications**
   - Go to Django Admin
   - Edit/add products with CCTV specifications
   - Refresh compare page to see specifications

---

## Timeline

- Created migration file: ✓
- Applied migration to database: ← PENDING
- Site works without errors: ← AFTER MIGRATION
- Can add specifications in admin: ← AFTER MIGRATION
- Specifications show on compare page: ← AFTER MIGRATION

---

## After Migration is Applied

### 1. Django Admin Will Show

When editing a product:
```
📦 Basic Information
💰 Inventory & Pricing
📷 CCTV Specifications (NEW - with 13 fields)
```

### 2. You Can Add Product Specs

```
Admin Panel → Store → Products → [Product] → Expand "CCTV Specifications"
```

### 3. Compare Page Works

When comparing products, specifications will display automatically.

---

## Troubleshooting Commands

```bash
# Check migration status
python manage.py showmigrations

# Apply all pending migrations
python manage.py migrate

# See detailed migration output
python manage.py migrate --verbosity=2

# Undo last migration (if needed)
python manage.py migrate store 0009_category_icon

# Check model fields
python manage.py shell
```

---

## Summary

✅ **What's Done**:
- Product model extended with 13 fields
- Admin panel organized with CCTV Specifications
- Specification builder updated
- Migration file created

⏳ **What's Needed**:
- Run `python manage.py migrate` to apply migration to database

✅ **What Happens After**:
- Site works without errors
- Can add CCTV specifications in Django Admin
- Compare page displays specifications automatically

---

## One-Command Fix

```bash
python manage.py migrate && echo "Migration applied successfully!"
```

This command:
1. Applies all pending migrations
2. Prints success message if no errors

Then refresh your browser at `http://127.0.0.1:8000/`

---

**Date**: March 10, 2026  
**Status**: Ready to fix - just run the migrate command!

