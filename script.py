from django.test import Client
from django.contrib.auth.models import User

c = Client()
user = User.objects.filter(is_superuser=True).first()
if getattr(user, 'pk', None) is None:
    user = User.objects.create_superuser('admin_test', 'admin@example.com', 'password')

c.force_login(user)
response = c.get('/admin-dashboard/', SERVER_NAME='127.0.0.1')

with open('debug_html.txt', 'wb') as f:
    f.write(response.content)
print("SUCCESS WRITING HTML")
