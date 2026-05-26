# Generated migration file for adding CCTV specification fields to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_category_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='camera_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('bullet', 'Bullet'),
                    ('dome', 'Dome'),
                    ('turret', 'Turret'),
                    ('ptz', 'PTZ'),
                    ('wireless', 'Wireless / WiFi'),
                    ('fisheye', 'Fisheye'),
                    ('cube', 'Indoor Cube'),
                ],
                help_text='Type of CCTV camera',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='resolution',
            field=models.CharField(
                blank=True,
                help_text='Resolution (e.g., 4K, 2MP, 5MP)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='night_vision_range',
            field=models.CharField(
                blank=True,
                help_text='Night vision range in meters (e.g., 30m)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='field_of_view',
            field=models.CharField(
                blank=True,
                help_text='Field of view in degrees (e.g., 90°)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='lens',
            field=models.CharField(
                blank=True,
                help_text='Lens specification (e.g., 3.6mm)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='frame_rate',
            field=models.CharField(
                blank=True,
                help_text='Frame rate (e.g., 30fps)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='weatherproof',
            field=models.CharField(
                blank=True,
                help_text='Weatherproof rating (e.g., IP66)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='connectivity',
            field=models.CharField(
                blank=True,
                choices=[
                    ('wired', 'Wired'),
                    ('wifi', 'Wi-Fi'),
                    ('hybrid', 'Hybrid'),
                ],
                help_text='Connectivity type',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='power_source',
            field=models.CharField(
                blank=True,
                choices=[
                    ('poe', 'PoE'),
                    ('dc12v', 'DC 12V'),
                    ('battery', 'Battery'),
                    ('solar', 'Solar'),
                ],
                help_text='Power source type',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='storage_support',
            field=models.CharField(
                blank=True,
                help_text='Storage options (e.g., NVR, microSD, Cloud)',
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='audio_support',
            field=models.BooleanField(
                default=False,
                help_text='Does this camera support audio?',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='ai_detection',
            field=models.BooleanField(
                default=False,
                help_text='Does this camera have AI detection?',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty',
            field=models.CharField(
                blank=True,
                help_text='Warranty period (e.g., 2 years)',
                max_length=50,
            ),
        ),
    ]
