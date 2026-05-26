import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Category, Product

try:
    c, created = Category.objects.get_or_create(
        slug='cctv-installations',
        defaults={'name': 'CCTV Installations (Service)'}
    )
    print("Category:", c, created)

    p, created = Product.objects.get_or_create(
        slug='complete-cctv-solution-installation',
        defaults={
            'category': c,
            'name': 'Complete CCTV Solution Installation',
            'price': 5000,
            'stock': 999,
            'is_available': True,
            'description': 'Get professional installation for your CCTV system.',
        }
    )
    print("Product:", p, created)
except Exception as e:
    import traceback
    traceback.print_exc()
