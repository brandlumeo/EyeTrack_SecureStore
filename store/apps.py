from django.apps import AppConfig


class StoreConfig(AppConfig):
    name = 'store'

    def ready(self):
        from . import signals  # noqa: F401  (WebP copies of uploaded photos)
