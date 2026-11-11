import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

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


class ServiceTicket(models.Model):
    """An after-sales service request raised by a customer from their account."""

    class Category(models.TextChoices):
        CAMERA_OFFLINE = "camera_offline", "Camera offline / no picture"
        RECORDING = "recording", "Recording or playback problem"
        MOBILE_VIEW = "mobile_view", "Mobile app / remote viewing"
        NIGHT_VISION = "night_vision", "Night vision or image quality"
        DAMAGE = "damage", "Physical damage or cabling"
        ACCESS_CONTROL = "access_control", "Smart lock / biometric / door phone"
        INSTALLATION = "installation", "Installation follow-up"
        OTHER = "other", "Something else"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        WAITING_CUSTOMER = "waiting_customer", "Waiting for your reply"
        VISIT_SCHEDULED = "visit_scheduled", "Technician visit scheduled"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENT = "urgent", "Urgent"

    OPEN_STATUSES = (Status.OPEN, Status.IN_PROGRESS, Status.WAITING_CUSTOMER, Status.VISIT_SCHEDULED)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="service_tickets")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="service_tickets")
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.CAMERA_OFFLINE)
    subject = models.CharField(max_length=150)
    description = models.TextField()
    contact_phone = models.CharField(max_length=20)
    site_location = models.CharField(max_length=200, blank=True, help_text="Area / city where the equipment is installed")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    assigned_technician = models.ForeignKey("orders.Technician", on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name="service_tickets")
    visit_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return "%s - %s" % (self.reference, self.subject)

    @property
    def reference(self):
        return "SR-%05d" % self.pk if self.pk else "SR-new"

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES


class TicketMessage(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ticket_messages")
    from_staff = models.BooleanField(default=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return "Message on %s" % self.ticket.reference


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name="attachments")
    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    image = models.ImageField(upload_to="service_tickets/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "id"]


class ViewingGuide(models.Model):
    """Step-by-step "watch your cameras on your phone" guide, edited by staff in the admin dashboard."""

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    brand = models.CharField(max_length=60, help_text="e.g. Hikvision, Dahua, CP Plus, or General")
    app_name = models.CharField(max_length=60, blank=True, help_text="e.g. Hik-Connect, DMSS, gCMOB")
    summary = models.CharField(max_length=250, help_text="One sentence shown on the guide list.")
    before_you_start = models.TextField(blank=True, help_text="Checklist, one item per line.")
    steps = models.TextField(help_text="One step per line, in order.")
    troubleshooting = models.TextField(blank=True, help_text="Problem and fix, one per line (e.g. 'Device offline: check the recorder's internet cable').")
    android_url = models.URLField(blank=True, help_text="Google Play link for the app (copy it from the Play Store).")
    ios_url = models.URLField(blank=True, help_text="App Store link for the app.")
    image = models.ImageField(upload_to="guides/", blank=True, help_text="Optional screenshot or diagram.")
    is_published = models.BooleanField(default=False, help_text="Only publish after checking the steps against the current app.")
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "brand", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:150] or "guide"
            slug, n = base, 2
            while ViewingGuide.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = "%s-%d" % (base, n), n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("guide_detail", args=[self.slug])

    @staticmethod
    def _lines(text):
        return [line.strip(" -\u2022\t") for line in text.splitlines() if line.strip(" -\u2022\t")]

    @property
    def step_list(self):
        return self._lines(self.steps)

    @property
    def checklist(self):
        return self._lines(self.before_you_start)

    @property
    def fixes(self):
        """Troubleshooting lines split into (problem, fix) at the first colon."""
        out = []
        for line in self._lines(self.troubleshooting):
            problem, sep, fix = line.partition(":")
            out.append((problem.strip(), fix.strip()) if sep else ("", line))
        return out


DOWNLOAD_EXTENSIONS = ["pdf", "zip", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"]


class Download(models.Model):
    """A manual, datasheet, brochure or software link listed in the download centre at /support/downloads/."""

    class Kind(models.TextChoices):
        MANUAL = "manual", "User manual"
        DATASHEET = "datasheet", "Datasheet"
        BROCHURE = "brochure", "Brochure"
        SOFTWARE = "software", "Software"
        APP = "app", "Mobile app"
        OTHER = "other", "Other"

    title = models.CharField(max_length=150)
    kind = models.CharField("type", max_length=20, choices=Kind.choices, default=Kind.MANUAL)
    brand = models.CharField(max_length=60, blank=True, help_text="e.g. Hikvision, Dahua, CP Plus. Leave blank for general documents.")
    description = models.CharField(max_length=250, blank=True)
    file = models.FileField(upload_to="downloads/", blank=True,
                            validators=[FileExtensionValidator(DOWNLOAD_EXTENSIONS)],
                            help_text="PDF, ZIP, Word, Excel or image, up to 25 MB.")
    external_url = models.URLField(blank=True, help_text="Or link to the manufacturer's download page instead of uploading a file.")
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "kind", "title"]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.file and not self.external_url:
            raise ValidationError("Upload a file or enter a link.")
        if self.file and self.external_url:
            raise ValidationError("Choose either a file or a link, not both.")

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("download_file", args=[self.pk])

    @property
    def is_external(self):
        return not self.file and bool(self.external_url)

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1].lstrip(".").upper() if self.file else ""

    @property
    def size_label(self):
        try:
            size = self.file.size if self.file else 0
        except OSError:
            return ""
        if not size:
            return ""
        return "%.1f MB" % (size / 1048576) if size >= 1048576 else "%d KB" % max(1, size // 1024)
