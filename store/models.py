from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Count
from django.utils.text import slugify
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self, *args, **kwargs):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class Category(SoftDeleteModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, default='bi-grid', help_text="Bootstrap icon class (e.g., bi-camera-video)")

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Soft delete products conditionally
        for product in self.products.all():
            product.delete()
        super().delete(*args, **kwargs)

    def restore(self, *args, **kwargs):
        for product in self.products.all_objects.filter(is_deleted=True):
            product.restore()
        super().restore(*args, **kwargs)


class Product(SoftDeleteModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", help_text="Product category (e.g., Dome Cameras, DVR Systems, etc.)")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    highlights = models.TextField(blank=True, help_text="Key features/highlights. Use new lines for bullets.")
    is_available = models.BooleanField(default=True)
    installation_available = models.BooleanField(default=False, help_text="Can this product be installed by our agents?")
    installation_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Installation charge per unit")
    is_free_shipping = models.BooleanField(default=False, help_text="If checked, this product will not contribute to shipping weight/charges.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # CCTV Specifications
    CAMERA_TYPE_CHOICES = [
        ("bullet", "Bullet"),
        ("dome", "Dome"),
        ("turret", "Turret"),
        ("ptz", "PTZ"),
        ("wireless", "Wireless / WiFi"),
        ("fisheye", "Fisheye"),
        ("cube", "Indoor Cube"),
        ("vdp", "Video Door Phone"),
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

    camera_type = models.CharField(
        max_length=20,
        choices=CAMERA_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of CCTV camera"
    )
    resolution = models.CharField(
        max_length=50,
        blank=True,
        help_text="Resolution (e.g., 4K, 2MP, 5MP)"
    )
    night_vision_range = models.CharField(
        max_length=50,
        blank=True,
        help_text="Night vision range in meters (e.g., 30m)"
    )
    field_of_view = models.CharField(
        max_length=50,
        blank=True,
        help_text="Field of view in degrees (e.g., 90°)"
    )
    lens = models.CharField(
        max_length=50,
        blank=True,
        help_text="Lens specification (e.g., 3.6mm)"
    )
    frame_rate = models.CharField(
        max_length=50,
        blank=True,
        help_text="Frame rate (e.g., 30fps)"
    )
    weatherproof = models.CharField(
        max_length=50,
        blank=True,
        help_text="Weatherproof rating (e.g., IP66)"
    )
    connectivity = models.CharField(
        max_length=20,
        choices=CONNECTIVITY_CHOICES,
        blank=True,
        null=True,
        help_text="Connectivity type"
    )
    power_source = models.CharField(
        max_length=20,
        choices=POWER_SOURCE_CHOICES,
        blank=True,
        null=True,
        help_text="Power source type"
    )
    storage_support = models.CharField(
        max_length=200,
        blank=True,
        help_text="Storage options (e.g., NVR, microSD, Cloud)"
    )
    audio_support = models.BooleanField(
        default=False,
        help_text="Does this camera support audio?"
    )
    ai_detection = models.BooleanField(
        default=False,
        help_text="Does this camera have AI detection?"
    )
    warranty = models.CharField(
        max_length=50,
        blank=True,
        help_text="Warranty period (e.g., 2 years)"
    )

    # Video Door Phone Specifications
    CONNECTIVITY_TYPE_CHOICES = [
        ("wired", "Wired"),
        ("wireless", "Wireless"),
        ("wifi", "Wi-Fi"),
        ("hybrid", "Hybrid"),
    ]
    UNLOCK_METHOD_CHOICES = [
        ("rfid", "RFID Card"),
        ("pin", "PIN Code"),
        ("fingerprint", "Fingerprint"),
        ("app", "Mobile App"),
        ("key", "Mechanical Key"),
        ("hybrid", "Multiple Methods"),
    ]
    POWER_SOURCE_VDP_CHOICES = [
        ("poe", "PoE"),
        ("dc12v", "DC 12V"),
        ("battery", "Battery"),
        ("hybrid", "Hybrid"),
    ]
    INSTALLATION_TYPE_CHOICES = [
        ("surface", "Surface Mount"),
        ("flush", "Flush Mount"),
        ("both", "Both"),
    ]

    screen_size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Screen size (e.g., 7 inch, 10.1 inch)"
    )
    camera_resolution = models.CharField(
        max_length=50,
        blank=True,
        help_text="Camera resolution (e.g., 2MP, 5MP)"
    )
    night_vision = models.BooleanField(
        default=False,
        help_text="Does this video door phone have night vision?"
    )
    connectivity_type = models.CharField(
        max_length=20,
        choices=CONNECTIVITY_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Connectivity type for the video door phone"
    )
    unlock_method = models.CharField(
        max_length=20,
        choices=UNLOCK_METHOD_CHOICES,
        blank=True,
        null=True,
        help_text="Primary unlock method"
    )
    audio_communication = models.BooleanField(
        default=True,
        help_text="Does this video door phone support audio communication?"
    )
    mobile_app_support = models.BooleanField(
        default=False,
        help_text="Does this video door phone support mobile app control?"
    )
    storage_support_vdp = models.CharField(
        max_length=200,
        blank=True,
        help_text="Storage options (e.g., microSD, Cloud, Local)"
    )
    power_source_vdp = models.CharField(
        max_length=20,
        choices=POWER_SOURCE_VDP_CHOICES,
        blank=True,
        null=True,
        help_text="Power source for the video door phone"
    )
    installation_type = models.CharField(
        max_length=20,
        choices=INSTALLATION_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Installation mounting type"
    )
    warranty_vdp = models.CharField(
        max_length=50,
        blank=True,
        help_text="Warranty period (e.g., 1 year, 2 years)"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def averageReview(self):
        from .models import Review
        reviews = Review.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        from .models import Review
        reviews = Review.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        cnt = 0
        if reviews['count'] is not None:
            cnt = int(reviews['count'])
        return cnt


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to='products/gallery/', help_text="Additional product image")

    class Meta:
        verbose_name = "Product Gallery Image"
        verbose_name_plural = "Product Gallery Images"

    def __str__(self):
        return f"{self.product.name} Gallery Image"



class CameraSpecification(models.Model):
    CAMERA_TYPE_CHOICES = [
        ("bullet", "Bullet"),
        ("dome", "Dome"),
        ("turret", "Turret"),
        ("ptz", "PTZ"),
        ("wireless", "Wireless / WiFi"),
        ("fisheye", "Fisheye"),
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

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="camera_specs")
    camera_type = models.CharField(max_length=20, choices=CAMERA_TYPE_CHOICES, blank=True, null=True)
    resolution_mp = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    lens_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    field_of_view_deg = models.PositiveSmallIntegerField(null=True, blank=True)
    night_vision_range_m = models.PositiveSmallIntegerField(null=True, blank=True)
    frame_rate_fps = models.PositiveSmallIntegerField(null=True, blank=True)
    weatherproof_rating = models.CharField(max_length=20, blank=True, help_text="Example: IP66")
    connectivity = models.CharField(max_length=20, choices=CONNECTIVITY_CHOICES, blank=True, null=True)
    power_source = models.CharField(max_length=20, choices=POWER_SOURCE_CHOICES, blank=True, null=True)
    storage_support = models.CharField(max_length=120, blank=True, help_text="Example: NVR, microSD, Cloud")
    audio_support = models.BooleanField(default=False)
    ai_detection = models.BooleanField(default=False)
    warranty_years = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - Camera Specs"


class BiometricSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="biometric_specs")
    authentication_method = models.CharField(max_length=100, blank=True, help_text="Example: Fingerprint, Face, RFID")
    user_capacity = models.PositiveIntegerField(null=True, blank=True)
    fingerprint_sensor = models.CharField(max_length=100, blank=True, help_text="Example: Optical, Capacitive")
    face_recognition = models.BooleanField(default=False)
    card_support = models.BooleanField(default=False, help_text="RFID/Mifare card support")
    connectivity = models.CharField(max_length=100, blank=True, help_text="Example: TCP/IP, Wi-Fi, USB")
    power_supply = models.CharField(max_length=50, blank=True, help_text="Example: 12V DC")

    def __str__(self):
        return f"{self.product.name} - Biometric Specs"


class SmartLockSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="smartlock_specs")
    unlock_methods = models.CharField(max_length=150, blank=True, help_text="Example: Fingerprint, PIN, App, Key")
    connectivity = models.CharField(max_length=100, blank=True, help_text="Example: Bluetooth, Wi-Fi, Zigbee")
    battery_life = models.CharField(max_length=100, blank=True, help_text="Example: 12 months")
    emergency_unlock = models.BooleanField(default=True, help_text="Mechanical key override / emergency power")

    def __str__(self):
        return f"{self.product.name} - Smart Lock Specs"


class NetworkDeviceSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="network_specs")
    ports = models.PositiveIntegerField(null=True, blank=True, help_text="Number of ports (e.g., 4, 8, 16, 24)")
    bandwidth = models.CharField(max_length=50, blank=True, help_text="Example: 10/100/1000 Mbps")
    poe_support = models.BooleanField(default=False, help_text="Power over Ethernet support")

    def __str__(self):
        return f"{self.product.name} - Network Specs"


class Wishlist(models.Model):
    """Stores a user's saved/wishlisted products."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} to {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.product.name}"

class ReviewMedia(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='reviews/', help_text="User uploaded photo or video for the review.")
    is_video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review Media"
        verbose_name_plural = "Review Media"

    def __str__(self):
        return f"Media for Review {self.review.id} ({'Video' if self.is_video else 'Photo'})"

class Coupon(SoftDeleteModel):
    """
    Model to store promotional codes.
    """
    code = models.CharField(max_length=50, unique=True, help_text="Promo code text (e.g., WINTER20)")
    discount_percentage = models.PositiveIntegerField(help_text="Discount percentage (e.g., 10 for 10%)")
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Maximum discount amount in currency (e.g., ₹500 cap)"
    )
    valid_from = models.DateTimeField(help_text="When does the coupon start being active?")
    valid_to = models.DateTimeField(help_text="When does the coupon expire?")
    active = models.BooleanField(default=True, help_text="Is the coupon currently usable?")
    max_uses = models.PositiveIntegerField(default=100, help_text="Total number of times this coupon can be used by all users combined")
    current_uses = models.PositiveIntegerField(default=0)

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.active:
            return False, "This coupon is no longer active."
        if self.current_uses >= self.max_uses:
            return False, "This coupon has reached its usage limit."
        if now < self.valid_from:
            return False, "This coupon is not valid yet."
        if now > self.valid_to:
            return False, "This coupon has expired."
        return True, "Valid"

    def __str__(self):
        return self.code


class ServiceableArea(models.Model):
    """
    Stores pincodes where company provides delivery and installation services.
    """
    pincode = models.CharField(max_length=6, unique=True, help_text="6-digit PIN code (e.g., 110001)")
    delivery_available = models.BooleanField(default=True)
    installation_available = models.BooleanField(default=True, help_text="Professional installation support in this area")
    estimated_delivery_days = models.PositiveIntegerField(default=5, help_text="Standard delivery time in days")
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Delivery charge for this specific pincode")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Serviceable Area"
        verbose_name_plural = "Serviceable Areas"
        ordering = ['pincode']

    def save(self, *args, **kwargs):
        if self.delivery_available:
            self.installation_available = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pincode} - Delivery: {self.delivery_available}"


class StockNotification(models.Model):
    """Captures emails of users who want to be notified when an out-of-stock product is back."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_notifications')
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'email')
        verbose_name = "Stock Notification"
        verbose_name_plural = "Stock Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} → {self.product.name}"


class ReviewHelpful(models.Model):
    """Tracks whether a visitor found a review helpful, keyed by session."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    session_key = models.CharField(max_length=40)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'session_key')
        verbose_name = "Review Helpful Vote"
        verbose_name_plural = "Review Helpful Votes"

    def __str__(self):
        return f"{'Helpful' if self.is_helpful else 'Not helpful'} on Review #{self.review.id}"


class Project(models.Model):
    """A completed installation shown in the public projects gallery."""

    class SiteType(models.TextChoices):
        HOME = "home", "Home / Villa"
        APARTMENT = "apartment", "Apartment / Flat"
        SHOP = "shop", "Shop / Retail"
        OFFICE = "office", "Office"
        FACTORY = "factory", "Factory / Warehouse"
        SCHOOL = "school", "School / Institution"
        HOSPITAL = "hospital", "Hospital / Clinic"
        OTHER = "other", "Other"

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    site_type = models.CharField(max_length=20, choices=SiteType.choices, default=SiteType.HOME)
    location = models.CharField(max_length=120, help_text="Area / city, e.g. Perambra, Kozhikode. Avoid exact addresses.")
    completed_on = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(upload_to="projects/%Y/%m/", help_text="Main photo. Only publish photos the customer has agreed to.")
    summary = models.CharField(max_length=300, help_text="One or two sentences shown on the gallery card.")
    challenge = models.TextField(blank=True, help_text="What the customer needed or the problem to solve.")
    solution = models.TextField(blank=True, help_text="What was installed and why.")
    cameras_installed = models.PositiveIntegerField(null=True, blank=True)
    system_details = models.TextField(blank=True, help_text="One item per line, e.g. 8 x 4MP turret cameras, 8-ch NVR, 4 TB HDD.")
    products = models.ManyToManyField(Product, blank=True, related_name="projects", help_text="Catalogue products used (optional).")
    testimonial = models.TextField(blank=True, help_text="Customer's own words, with their permission.")
    testimonial_author = models.CharField(max_length=120, blank=True, help_text="e.g. Shop owner, Perambra")
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text="Show on the homepage.")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-completed_on", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:150] or "project"
            slug, n = base, 2
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = "%s-%d" % (base, n), n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("project_detail", args=[self.slug])

    @property
    def system_lines(self):
        return [line.strip(" -•") for line in self.system_details.splitlines() if line.strip(" -•")]


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="projects/%Y/%m/")
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or "Photo of %s" % self.project
