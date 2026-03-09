from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CAMERA_TYPE_CHOICES = [
        ("bullet", "Bullet"),
        ("dome", "Dome"),
        ("turret", "Turret"),
        ("ptz", "PTZ"),
        ("cube", "Indoor Cube"),
    ]
    CONNECTIVITY_CHOICES = [
        ("wired", "Wired"),
        ("wifi", "Wi-Fi"),
        ("hybrid", "Hybrid"),
    ]
    POWER_SOURCE_CHOICES = [
        ("poe", "PoE"),
        ("dc12v", "DC 12V"),
        ("battery", "Battery"),
        ("solar", "Solar"),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    camera_type = models.CharField(max_length=20, choices=CAMERA_TYPE_CHOICES, blank=True)
    resolution_mp = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    lens_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    field_of_view_deg = models.PositiveSmallIntegerField(null=True, blank=True)
    night_vision_range_m = models.PositiveSmallIntegerField(null=True, blank=True)
    frame_rate_fps = models.PositiveSmallIntegerField(null=True, blank=True)
    weatherproof_rating = models.CharField(max_length=20, blank=True, help_text="Example: IP66")
    connectivity = models.CharField(max_length=20, choices=CONNECTIVITY_CHOICES, blank=True)
    power_source = models.CharField(max_length=20, choices=POWER_SOURCE_CHOICES, blank=True)
    storage_support = models.CharField(max_length=120, blank=True, help_text="Example: NVR, microSD, Cloud")
    audio_support = models.BooleanField(default=False)
    ai_detection = models.BooleanField(default=False)
    warranty_years = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
