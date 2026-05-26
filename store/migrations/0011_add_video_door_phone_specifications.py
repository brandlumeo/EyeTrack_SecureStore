# Generated migration file for adding Video Door Phone specification fields to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_add_cctv_specifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='audio_communication',
            field=models.BooleanField(
                default=True,
                help_text='Does this video door phone support audio communication?',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='camera_resolution',
            field=models.CharField(
                blank=True,
                help_text='Camera resolution (e.g., 2MP, 5MP)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='connectivity_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('wired', 'Wired'),
                    ('wireless', 'Wireless'),
                    ('wifi', 'Wi-Fi'),
                    ('hybrid', 'Hybrid'),
                ],
                help_text='Connectivity type for the video door phone',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='installation_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('surface', 'Surface Mount'),
                    ('flush', 'Flush Mount'),
                    ('both', 'Both'),
                ],
                help_text='Installation mounting type',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='mobile_app_support',
            field=models.BooleanField(
                default=False,
                help_text='Does this video door phone support mobile app control?',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='night_vision',
            field=models.BooleanField(
                default=False,
                help_text='Does this video door phone have night vision?',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='power_source_vdp',
            field=models.CharField(
                blank=True,
                choices=[
                    ('poe', 'PoE'),
                    ('dc12v', 'DC 12V'),
                    ('battery', 'Battery'),
                    ('hybrid', 'Hybrid'),
                ],
                help_text='Power source for the video door phone',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='screen_size',
            field=models.CharField(
                blank=True,
                help_text='Screen size (e.g., 7 inch, 10.1 inch)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='storage_support_vdp',
            field=models.CharField(
                blank=True,
                help_text='Storage options (e.g., microSD, Cloud, Local)',
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='unlock_method',
            field=models.CharField(
                blank=True,
                choices=[
                    ('rfid', 'RFID Card'),
                    ('pin', 'PIN Code'),
                    ('fingerprint', 'Fingerprint'),
                    ('app', 'Mobile App'),
                    ('key', 'Mechanical Key'),
                    ('hybrid', 'Multiple Methods'),
                ],
                help_text='Primary unlock method',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty_vdp',
            field=models.CharField(
                blank=True,
                help_text='Warranty period (e.g., 1 year, 2 years)',
                max_length=50,
            ),
        ),
    ]
