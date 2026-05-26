import os
import django
from django.test import Client
from django.contrib.auth.models import User

c = Client()
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.create_superuser('admin_test', 'admin@example.com', 'password')

c.force_login(user)

response = c.get('/admin-dashboard/')
html = response.content.decode('utf-8')

import json
with open('debug_html.txt', 'w', encoding='utf-8') as f:
    f.write(html)
