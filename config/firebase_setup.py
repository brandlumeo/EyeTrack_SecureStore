import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials
except ModuleNotFoundError:
    firebase_admin = None
    credentials = None


def is_firebase_ready():
    return firebase_admin is not None and bool(firebase_admin._apps)


def initialize_firebase():
    if firebase_admin is None:
        logger.warning("firebase_admin is not installed. Firebase features are disabled.")
        return False

    if firebase_admin._apps:
        return True

    cred_path = os.path.join(settings.BASE_DIR, "firebase-credentials.json")
    if not os.path.exists(cred_path):
        logger.warning("firebase-credentials.json not found. Firebase Admin SDK will not initialize.")
        return False

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    return True
