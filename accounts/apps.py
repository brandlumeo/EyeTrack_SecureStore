from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from config.firebase_setup import initialize_firebase
        initialize_firebase()
