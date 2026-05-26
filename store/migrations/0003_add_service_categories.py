# Generated migration to add comprehensive security product and service categories

from django.db import migrations


def add_categories(apps, schema_editor):
    """Add comprehensive security product and service categories"""
    Category = apps.get_model('store', 'Category')
    
    categories_data = [
        # CCTV Camera Products
        {
            'name': 'Dome Cameras',
            'slug': 'dome-cameras'
        },
        {
            'name': 'Bullet Cameras',
            'slug': 'bullet-cameras'
        },
        {
            'name': 'PTZ Cameras',
            'slug': 'ptz-cameras'
        },
        {
            'name': 'Turret Cameras',
            'slug': 'turret-cameras'
        },
        {
            'name': 'Wireless / WiFi Cameras',
            'slug': 'wireless-wifi-cameras'
        },
        {
            'name': 'Fisheye Cameras',
            'slug': 'fisheye-cameras'
        },
        # Recording Devices
        {
            'name': 'DVR Systems',
            'slug': 'dvr-systems'
        },
        {
            'name': 'NVR Systems',
            'slug': 'nvr-systems'
        },
        # Access Control
        {
            'name': 'Smart Locks',
            'slug': 'smart-locks'
        },
        {
            'name': 'Biometric Devices',
            'slug': 'biometric-devices'
        },
        # Automation
        {
            'name': 'Home/Gate Automation',
            'slug': 'home-gate-automation'
        },
        # Services
        {
            'name': 'CCTV Installations',
            'slug': 'cctv-installations'
        },
        # Other Security Products
        {
            'name': 'Other Security Products',
            'slug': 'other-security-products'
        },
    ]
    
    for category_data in categories_data:
        Category.objects.get_or_create(
            slug=category_data['slug'],
            defaults={'name': category_data['name']}
        )


def remove_categories(apps, schema_editor):
    """Remove the added categories in case of rollback"""
    Category = apps.get_model('store', 'Category')
    Category.objects.filter(
        slug__in=[
            'dome-cameras',
            'bullet-cameras',
            'ptz-cameras',
            'turret-cameras',
            'wireless-wifi-cameras',
            'fisheye-cameras',
            'dvr-systems',
            'nvr-systems',
            'smart-locks',
            'biometric-devices',
            'home-gate-automation',
            'cctv-installations',
            'other-security-products'
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_product_specs'),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]