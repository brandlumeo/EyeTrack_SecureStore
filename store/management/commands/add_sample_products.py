from django.core.management.base import BaseCommand
from store.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Add sample security products to the store'

    def handle(self, *args, **options):
        # Sample products data
        products_data = [
            # Dome Cameras
            {
                'name': 'Hikvision Dome 2MP',
                'category_slug': 'dome-cameras',
                'description': 'Professional 2MP dome camera with night vision and weatherproof rating IP66. Ideal for outdoor surveillance.',
                'camera_type': 'dome',
                'resolution_mp': Decimal('2.0'),
                'lens_mm': Decimal('3.6'),
                'field_of_view_deg': 90,
                'night_vision_range_m': 30,
                'frame_rate_fps': 25,
                'weatherproof_rating': 'IP66',
                'connectivity': 'wired',
                'power_source': 'poe',
                'storage_support': 'NVR, microSD',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 2,
                'price': Decimal('4500.00'),
                'stock': 15,
                'is_available': True,
            },
            {
                'name': 'Dahua 4MP Smart Dome',
                'category_slug': 'dome-cameras',
                'description': 'Advanced 4MP turret dome camera with AI-powered detection. Supports cloud and local storage.',
                'camera_type': 'dome',
                'resolution_mp': Decimal('4.0'),
                'lens_mm': Decimal('2.8'),
                'field_of_view_deg': 110,
                'night_vision_range_m': 40,
                'frame_rate_fps': 30,
                'weatherproof_rating': 'IP67',
                'connectivity': 'wifi',
                'power_source': 'dc12v',
                'storage_support': 'Cloud, microSD, NVR',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 3,
                'price': Decimal('6800.00'),
                'stock': 10,
                'is_available': True,
            },
            # Bullet Cameras
            {
                'name': 'CP Plus 5MP Bullet',
                'category_slug': 'bullet-cameras',
                'description': 'Heavy-duty 5MP bullet camera designed for long-range surveillance. Vandal-resistant design.',
                'camera_type': 'bullet',
                'resolution_mp': Decimal('5.0'),
                'lens_mm': Decimal('3.6'),
                'field_of_view_deg': 85,
                'night_vision_range_m': 50,
                'frame_rate_fps': 30,
                'weatherproof_rating': 'IP67',
                'connectivity': 'wired',
                'power_source': 'poe',
                'storage_support': 'NVR, DVR',
                'audio_support': False,
                'ai_detection': False,
                'warranty_years': 2,
                'price': Decimal('5200.00'),
                'stock': 12,
                'is_available': True,
            },
            {
                'name': 'Hikvision 8MP Bullet Pro',
                'category_slug': 'bullet-cameras',
                'description': 'Professional 8MP bullet camera with advanced compression. Perfect for highways and entry points.',
                'camera_type': 'bullet',
                'resolution_mp': Decimal('8.0'),
                'lens_mm': Decimal('4.0'),
                'field_of_view_deg': 80,
                'night_vision_range_m': 60,
                'frame_rate_fps': 30,
                'weatherproof_rating': 'IP66',
                'connectivity': 'wired',
                'power_source': 'poe',
                'storage_support': 'NVR, microSD',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 2,
                'price': Decimal('8500.00'),
                'stock': 8,
                'is_available': True,
            },
            # PTZ Cameras
            {
                'name': 'Hikvision PTZ 2MP',
                'category_slug': 'ptz-cameras',
                'description': 'Pan-Tilt-Zoom camera with 20x optical zoom. Ideal for monitoring large areas.',
                'camera_type': 'ptz',
                'resolution_mp': Decimal('2.0'),
                'lens_mm': Decimal('4.7'),
                'field_of_view_deg': 60,
                'night_vision_range_m': 100,
                'frame_rate_fps': 25,
                'weatherproof_rating': 'IP66',
                'connectivity': 'wired',
                'power_source': 'poe',
                'storage_support': 'NVR',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 2,
                'price': Decimal('12000.00'),
                'stock': 5,
                'is_available': True,
            },
            # DVR Systems
            {
                'name': '8 Channel DVR System',
                'category_slug': 'dvr-systems',
                'description': 'Professional 8-channel DVR with 4K output support. Includes 1TB HDD.',
                'resolution_mp': Decimal('5.0'),
                'connectivity': 'wired',
                'power_source': 'dc12v',
                'storage_support': 'HDD, microSD',
                'audio_support': True,
                'warranty_years': 2,
                'price': Decimal('8999.00'),
                'stock': 7,
                'is_available': True,
            },
            {
                'name': '16 Channel DVR Pro',
                'category_slug': 'dvr-systems',
                'description': '16-channel professional DVR with 5MP camera support. 2TB HDD included.',
                'resolution_mp': Decimal('5.0'),
                'connectivity': 'wired',
                'power_source': 'dc12v',
                'storage_support': 'HDD, RAID',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 3,
                'price': Decimal('15999.00'),
                'stock': 5,
                'is_available': True,
            },
            # NVR Systems
            {
                'name': '8 Channel NVR System',
                'category_slug': 'nvr-systems',
                'description': 'Network Video Recorder supporting 8 IP cameras. Cloud integration ready.',
                'resolution_mp': Decimal('5.0'),
                'connectivity': 'wired',
                'power_source': 'dc12v',
                'storage_support': 'HDD, Cloud, NAS',
                'audio_support': True,
                'warranty_years': 2,
                'price': Decimal('12500.00'),
                'stock': 6,
                'is_available': True,
            },
            {
                'name': '32 Channel NVR Enterprise',
                'category_slug': 'nvr-systems',
                'description': 'Enterprise-grade 32-channel NVR. Supports 8MP cameras with advanced analytics.',
                'resolution_mp': Decimal('8.0'),
                'connectivity': 'wired',
                'power_source': 'ac110v',
                'storage_support': 'HDD, RAID, Cloud',
                'audio_support': True,
                'ai_detection': True,
                'warranty_years': 3,
                'price': Decimal('45000.00'),
                'stock': 3,
                'is_available': True,
            },
            # Smart Locks
            {
                'name': 'Smart Door Lock Pro',
                'category_slug': 'smart-locks',
                'description': 'Biometric smart lock with fingerprint and RFID. WiFi and Bluetooth enabled.',
                'warranty_years': 2,
                'price': Decimal('4500.00'),
                'stock': 20,
                'is_available': True,
            },
            # Biometric Devices
            {
                'name': 'Fingerprint Time Attendance System',
                'category_slug': 'biometric-devices',
                'description': 'Professional fingerprint reader with real-time attendance tracking. Supports 5000 users.',
                'warranty_years': 2,
                'price': Decimal('8500.00'),
                'stock': 10,
                'is_available': True,
            },
            # Home/Gate Automation
            {
                'name': 'Smart Gate Opener System',
                'category_slug': 'home-gate-automation',
                'description': 'Automated gate opener with mobile control. Weather-resistant design.',
                'warranty_years': 2,
                'price': Decimal('12000.00'),
                'stock': 8,
                'is_available': True,
            },
            # CCTV Installation Service
            {
                'name': 'CCTV System Installation (2-4 Cameras)',
                'category_slug': 'cctv-installations',
                'description': 'Professional installation service for 2-4 camera CCTV systems. Includes setup, testing, and documentation.',
                'warranty_years': 1,
                'price': Decimal('5000.00'),
                'stock': 100,
                'is_available': True,
            },
            {
                'name': 'Complete CCTV Solution (8+ Cameras)',
                'category_slug': 'cctv-installations',
                'description': 'Full CCTV system installation for 8 or more cameras with DVR/NVR. Includes free maintenance for 1 year.',
                'warranty_years': 1,
                'price': Decimal('25000.00'),
                'stock': 50,
                'is_available': True,
            },
        ]

        created_count = 0
        for product_data in products_data:
            category_slug = product_data.pop('category_slug')
            category = Category.objects.get(slug=category_slug)
            
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=category,
                defaults=product_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {product.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Already exists: {product.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully created {created_count} sample products!')
        )
