import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Profile
from firebase_admin import messaging

p = Profile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='').first()
if not p:
    print("No token found")
    exit()

print("Found token:", p.fcm_token)

msg = messaging.Message(
    notification=messaging.Notification(
        title='Eyetrack Update',
        body='Test Notification'
    ),
    token=p.fcm_token
)

try:
    response = messaging.send(msg)
    print("Success! Response:", response)
except Exception as e:
    print("Failed!")
    print("Error:", str(e))
    import traceback
    traceback.print_exc()
