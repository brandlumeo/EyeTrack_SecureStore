from django.apps import AppConfig


class StoreConfig(AppConfig):
    name = 'store'

    def ready(self):
        import mimetypes
        mimetypes.add_type("image/webp", ".webp")  # not known to every Python/OS; FileResponse needs it
        from . import signals  # noqa: F401  (uploads stored as WebP, plus resized copies)
