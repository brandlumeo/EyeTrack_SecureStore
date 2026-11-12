"""Manually send one Firebase test push notification to the first profile that has an FCM token.

This contacts a real customer's device, so it only runs when executed directly and after confirmation:

    python scripts/send_test_push.py

(Previously test_fcm.py in the project root, where `manage.py test` imported and ran it.)
"""
import os
import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, for config.settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()

    from accounts.models import Profile
    from firebase_admin import messaging

    p = Profile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='').select_related('user').first()
    if not p:
        print("No token found")
        return

    token = p.fcm_token
    print("Found token for user %s: %s...%s" % (p.user.get_username(), token[:8], token[-6:]))
    if input("Send a real test notification to this device? Type 'yes' to continue: ").strip().lower() != 'yes':
        print("Cancelled.")
        return

    msg = messaging.Message(
        notification=messaging.Notification(
            title='Eyetrack Update',
            body='Test Notification'
        ),
        token=token
    )

    try:
        response = messaging.send(msg)
        print("Success! Response:", response)
    except Exception as e:
        print("Failed!")
        print("Error:", str(e))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
