from django.db import models

class FAQCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="bi-question-circle", help_text="Bootstrap icon class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "FAQ Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

class FAQ(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.question


class QuoteRequest(models.Model):
    """Site survey / quotation lead captured from the storefront."""

    class SiteType(models.TextChoices):
        HOME = "home", "Home / Villa"
        APARTMENT = "apartment", "Apartment / Flat"
        SHOP = "shop", "Shop / Retail"
        OFFICE = "office", "Office"
        FACTORY = "factory", "Factory / Warehouse"
        SCHOOL = "school", "School / Institution"
        HOSPITAL = "hospital", "Hospital / Clinic"
        OTHER = "other", "Other"

    class CameraCount(models.TextChoices):
        UP_TO_4 = "1-4", "1 - 4 cameras"
        UP_TO_8 = "5-8", "5 - 8 cameras"
        UP_TO_16 = "9-16", "9 - 16 cameras"
        ABOVE_16 = "16+", "More than 16"
        NOT_SURE = "unsure", "Not sure - advise me"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        SURVEY_SCHEDULED = "survey", "Survey Scheduled"
        QUOTED = "quoted", "Quote Sent"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    site_type = models.CharField(max_length=20, choices=SiteType.choices, default=SiteType.HOME)
    camera_count = models.CharField(max_length=10, choices=CameraCount.choices, default=CameraCount.NOT_SURE)
    pincode = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Area / city")
    message = models.TextField(blank=True)
    package = models.CharField(max_length=120, blank=True, help_text="Package selected on the storefront, if any")
    source_page = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.get_site_type_display()}"

    @property
    def whatsapp_number(self):
        digits = "".join(ch for ch in self.phone if ch.isdigit())
        if len(digits) == 10:
            digits = "91" + digits
        return digits
