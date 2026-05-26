# Generated migration to fix decimal field validation errors

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_alter_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='camera_type',
            field=models.CharField(blank=True, choices=[('bullet', 'Bullet'), ('dome', 'Dome'), ('turret', 'Turret'), ('ptz', 'PTZ'), ('wireless', 'Wireless / WiFi'), ('fisheye', 'Fisheye'), ('cube', 'Indoor Cube')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='connectivity',
            field=models.CharField(blank=True, choices=[('wired', 'Wired'), ('wifi', 'Wi-Fi'), ('hybrid', 'Hybrid')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='power_source',
            field=models.CharField(blank=True, choices=[('poe', 'PoE'), ('dc12v', 'DC 12V'), ('battery', 'Battery'), ('solar', 'Solar')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='lens_mm',
            field=models.DecimalField(blank=True, decimal_places=1, default=None, max_digits=4, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='resolution_mp',
            field=models.DecimalField(blank=True, decimal_places=1, default=None, max_digits=4, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(help_text='Product category (e.g., Dome Cameras, DVR Systems, etc.)', on_delete=models.deletion.CASCADE, related_name='products', to='store.category'),
        ),
    ]
