import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EyeTrack_SecureStore.settings")
django.setup()

from store.models import Product, CameraSpecification
from admin_dashboard.forms import CameraSpecForm

try:
    product = Product.objects.get(id=12)
    print(f"Product: {product.name}")
    print(f"Category: {product.category.name}")
    print(f"Category Slug: {product.category.slug}")
    
    spec_instance = None
    try:
        spec_instance = product.camera_specs
        print(f"Camera Specs Found (ID: {spec_instance.id})")
        print(f"Type: {spec_instance.camera_type}")
        print(f"Resolution: {spec_instance.resolution_mp}")
        print(f"Night Vision: {spec_instance.night_vision_range_m}")
    except Exception as e:
        print(f"Error accessing camera_specs directly: {type(e).__name__} - {e}")
        
    s_form = getattr(product, 'camera_specs', None)
    print(f"Result of getattr(product, 'camera_specs', None): {s_form}")
    
    form = CameraSpecForm(instance=s_form)
    print(f"Form initials: {form.initial}")
    
except Exception as e:
    print(f"Overall Error: {e}")
