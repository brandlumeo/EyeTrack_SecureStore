"""Make the storefront WebP copies for photos that are already uploaded.

    python manage.py make_thumbnails            # only photos missing copies
    python manage.py make_thumbnails --force    # remake every copy

New uploads get their copies automatically when saved; run this once after
deploying, and again with --force if store.images.WIDTHS or QUALITY change.
"""
from django.core.management.base import BaseCommand

from store import images
from store.signals import thumb_targets


class Command(BaseCommand):
    help = "Make resized WebP copies of product, project and installation photos."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Remake copies that already exist.")

    def handle(self, *args, force=False, **options):
        done = failed = 0
        for model, fields in thumb_targets():
            manager = getattr(model, "all_objects", model._default_manager)  # include soft-deleted
            for obj in manager.all().iterator():
                for field in fields:
                    f = getattr(obj, field)
                    if not f or not f.name:
                        continue
                    if images.make_thumbs(f, force=force):
                        done += 1
                    else:
                        failed += 1
                        self.stderr.write("No copies for %s (%s #%s)" % (f.name, model.__name__, obj.pk))
        self.stdout.write(self.style.SUCCESS("Photos with WebP copies: %d; skipped/failed: %d" % (done, failed)))
