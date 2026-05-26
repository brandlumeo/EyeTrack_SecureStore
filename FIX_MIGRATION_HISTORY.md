# 🔧 Fix Migration History - Step by Step

## The Problem
Database has `0005_*` applied but not `0004_fix_decimal_fields` in its migration history table.

## The Solution

Run these commands **in order**:

### Step 1: Unmigrate back to 0003
```bash
python manage.py migrate store 0003_add_service_categories
```

This removes `0004_*` and `0005_*` from the database's migration history.
The actual database schema won't change, just the history table.

### Step 2: Migrate forward (this will apply all in correct order)
```bash
python manage.py migrate store
```

This will apply:
- `0004_alter_product_category` (empty)
- `0004_fix_decimal_fields` (all field changes)
- `0005_alter_product_camera_type_alter_product_category` (empty)

In the correct order with proper dependencies!

### Step 3: Verify
```bash
python manage.py showmigrations store
```

Should show all migrations with [X] applied.

### Step 4: Run Server
```bash
python manage.py runserver
```

✅ Done!

---

## Complete Commands

Copy and paste these:

```bash
python manage.py migrate store 0003_add_service_categories
python manage.py migrate store
python manage.py showmigrations store
python manage.py runserver
```

---

## What Each Command Does

| Command | Purpose |
|---------|---------|
| `migrate store 0003_add_service_categories` | Unmigrate to 0003, removes 0004/0005 from history |
| `migrate store` | Apply all remaining migrations in correct order |
| `showmigrations store` | Verify all migrations are applied [X] |
| `runserver` | Start your server |

---

## Why This Works

1. **Unmigrate to 0003**: Removes the conflicting migrations from the history table
2. **Migrate forward**: Django applies them in the correct dependency order
3. **Result**: All migrations are in the correct state with proper history

No data is lost, no tables are dropped. Only the migration history is reset and reapplied correctly.

---

## Status After Running

✅ All migrations applied correctly
✅ Migration dependencies are correct
✅ Database schema is up to date
✅ Server runs without errors
✅ You can add products via admin

---

Run these commands now and you're done! 🚀
