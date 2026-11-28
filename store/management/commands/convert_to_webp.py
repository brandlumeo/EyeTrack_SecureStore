"""Convert photos that are already uploaded to WebP.

    python manage.py convert_to_webp --dry-run   # list what would change
    python manage.py convert_to_webp             # convert and update the database

Each JPG/PNG/GIF upload gets a WebP version next to it (same name, .webp) and
the database is pointed at it. Originals are kept unless --delete-originals is
given. New uploads are converted automatically (store.signals), so this only
needs running once per server. Safe to re-run: WebP files are skipped.
"""
from django.core.management.base import BaseCommand

from store import images
from store.signals import thumb_targets, webp_targets


class Command(BaseCommand):
    help = "Convert uploaded JPG/PNG/GIF photos to WebP and update the database."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list the files that would be converted.")
        parser.add_argument("--delete-originals", action="store_true", help="Delete the JPG/PNG files after converting.")

    def handle(self, *args, dry_run=False, delete_originals=False, **options):
        converted = {}  # (storage, old name) -> new name; files shared by several rows
        rows = failed = 0
        thumbed = {m: flds for m, flds in thumb_targets()}  # storefront photos get resized copies
        for model, fields in webp_targets():
            manager = getattr(model, "all_objects", model._default_manager)  # include soft-deleted
            for obj in manager.only("pk", *fields).iterator():
                for field in fields:
                    f = getattr(obj, field)
                    if not f or not images.needs_webp(f.name):
                        continue
                    if dry_run:
                        self.stdout.write("%s #%s %s: %s" % (model.__name__, obj.pk, field, f.name))
                        rows += 1
                        continue
                    key = (id(f.storage), f.name)
                    if key not in converted:
                        converted[key] = (f.storage, images.convert_stored(f))
                    new = converted[key][1]
                    if not new:
                        failed += 1
                        self.stderr.write("Could not convert %s (%s #%s)" % (f.name, model.__name__, obj.pk))
                        continue
                    manager.filter(pk=obj.pk).update(**{field: new})  # no save(): keeps timestamps
                    setattr(obj, field, new)
                    if field in thumbed.get(model, ()):
                        images.make_thumbs(getattr(obj, field))
                    rows += 1
                    self.stdout.write("%s -> %s" % (f.name, new))

        if delete_originals and not dry_run:
            for (_sid, old), (storage, new) in converted.items():
                if new:
                    try:
                        storage.delete(old)
                    except Exception as exc:
                        self.stderr.write("Could not delete %s: %s" % (old, exc))

        verb = "Would convert" if dry_run else "Converted"
        self.stdout.write(self.style.SUCCESS("%s %d photo field(s); failed: %d" % (verb, rows, failed)))
