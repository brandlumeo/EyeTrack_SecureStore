from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Product, Coupon


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"

    class ShippingStatus(models.TextChoices):
        NOT_SHIPPED = "not_shipped", "Not Shipped"
        PACKED = "packed", "Packed"
        IN_TRANSIT = "in_transit", "In Transit"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out For Delivery"
        DELIVERED = "delivered", "Delivered"

    class PaymentStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAID = "Paid", "Paid"
        FAILED = "Failed", "Failed"
        REFUNDED = "Refunded", "Refunded"

    class PaymentMethod(models.TextChoices):
        ONLINE = "online", "Online Payment"
        COD = "cod", "Cash On Delivery"

    PAYMENT_STATUS_CHOICES = PaymentStatus.choices

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_installation_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ONLINE,
    )
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    shipping_status = models.CharField(
        max_length=20,
        choices=ShippingStatus.choices,
        default=ShippingStatus.NOT_SHIPPED,
    )
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    order_notes = models.TextField(blank=True, null=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_order_status = self.order_status

    @property
    def status(self):
        return self.get_order_status_display()

    @status.setter
    def status(self, value):
        self.order_status = self.normalize_order_status(value)

    @classmethod
    def normalize_order_status(cls, value):
        if value in dict(cls.OrderStatus.choices):
            return value
        if not value:
            return cls.OrderStatus.PENDING

        normalized = str(value).strip().lower()
        legacy_map = {
            "pending": cls.OrderStatus.PENDING,
            "confirmed": cls.OrderStatus.CONFIRMED,
            "processing": cls.OrderStatus.PROCESSING,
            "shipped": cls.OrderStatus.SHIPPED,
            "delivered": cls.OrderStatus.DELIVERED,
            "completed": cls.OrderStatus.DELIVERED,
            "cancelled": cls.OrderStatus.CANCELLED,
            "canceled": cls.OrderStatus.CANCELLED,
            "returned": cls.OrderStatus.RETURNED,
        }
        return legacy_map.get(normalized, cls.OrderStatus.PENDING)

    @classmethod
    def normalize_shipping_status(cls, value):
        if value in dict(cls.ShippingStatus.choices):
            return value
        if not value:
            return cls.ShippingStatus.NOT_SHIPPED

        normalized = str(value).strip().lower().replace("-", " ").replace("_", " ")
        legacy_map = {
            "pending": cls.ShippingStatus.NOT_SHIPPED,
            "not shipped": cls.ShippingStatus.NOT_SHIPPED,
            "packed": cls.ShippingStatus.PACKED,
            "shipped": cls.ShippingStatus.IN_TRANSIT,
            "in transit": cls.ShippingStatus.IN_TRANSIT,
            "out for delivery": cls.ShippingStatus.OUT_FOR_DELIVERY,
            "delivered": cls.ShippingStatus.DELIVERED,
            "returned": cls.ShippingStatus.DELIVERED,
        }
        return legacy_map.get(normalized, cls.ShippingStatus.NOT_SHIPPED)

    @classmethod
    def normalize_payment_status(cls, value):
        if value in dict(cls.PaymentStatus.choices):
            return value
        if not value:
            return cls.PaymentStatus.PENDING

        normalized = str(value).strip().lower()
        legacy_map = {
            "pending": cls.PaymentStatus.PENDING,
            "paid": cls.PaymentStatus.PAID,
            "failed": cls.PaymentStatus.FAILED,
            "refunded": cls.PaymentStatus.REFUNDED,
        }
        return legacy_map.get(normalized, cls.PaymentStatus.PENDING)

    def save(self, *args, **kwargs):
        self.order_status = self.normalize_order_status(self.order_status)
        self.payment_status = self.normalize_payment_status(self.payment_status)
        self.shipping_status = self.normalize_shipping_status(self.shipping_status)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.formatted_id} - {self.full_name}"

    @property
    def formatted_id(self):
        """Returns a professional-looking order ID based on the primary key."""
        return f"ETR-{self.id:06d}"

    @property
    def return_deadline(self):
        """Returns the deadline for requesting a return (5 days after delivery)."""
        shipment = getattr(self, 'shipment', None)
        if shipment and shipment.delivered_at:
            return shipment.delivered_at + timezone.timedelta(days=5)
        # Fallback to 5 days after order if shipment delivered_at is missing for some reason
        if self.order_status == self.OrderStatus.DELIVERED:
             return self.updated_at + timezone.timedelta(days=5)
        return None

    @property
    def is_returnable(self):
        """Checks if the order is eligible for return."""
        if self.order_status != self.OrderStatus.DELIVERED:
            return False
        
        deadline = self.return_deadline
        if not deadline:
            return False
            
        return timezone.now() <= deadline


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    has_installation = models.BooleanField(default=False)
    installation_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('Simulation', 'Simulation'),
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Razorpay', 'Razorpay'),
        ('Stripe', 'Stripe'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Order.PaymentStatus.choices,
        default=Order.PaymentStatus.PENDING,
    )
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='Simulation')
    transaction_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order_id} - {self.status}"


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    payment_status = models.CharField(
        max_length=20,
        choices=Order.PaymentStatus.choices,
        default=Order.PaymentStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.invoice_number

    @staticmethod
    def build_invoice_number(order_id):
        return f"INV-{order_id:08d}"

    @classmethod
    def _quantize(cls, value):
        return Decimal(value).quantize(Decimal("0.01"))

    @classmethod
    def _get_payment_status(cls, order):
        latest_payment = order.payments.order_by("-created_at", "-id").first()
        source_status = latest_payment.status if latest_payment else order.payment_status
        return Order.normalize_payment_status(source_status)

    @classmethod
    def calculate_breakdown_for_order(cls, order):
        subtotal = sum(
            (item.price * item.quantity for item in order.items.all()),
            Decimal("0.00"),
        )
        subtotal = cls._quantize(subtotal)
        tax = cls._quantize(subtotal * Decimal("0.18"))
        total_amount = cls._quantize(order.total or Decimal("0.00"))
        calculated_shipping = total_amount - subtotal - tax
        if calculated_shipping < Decimal("0.00"):
            calculated_shipping = Decimal("0.00")

        return {
            "user": order.user,
            "subtotal": subtotal,
            "tax": tax,
            "shipping_cost": cls._quantize(calculated_shipping),
            "total_amount": total_amount,
            "payment_status": cls._get_payment_status(order),
        }

    @classmethod
    def sync_for_order(cls, order):
        if not order or not order.pk:
            return None

        defaults = {
            "invoice_number": cls.build_invoice_number(order.pk),
            **cls.calculate_breakdown_for_order(order),
        }
        invoice, created = cls.objects.get_or_create(order=order, defaults=defaults)
        if created:
            return invoice

        changed_fields = []
        for field_name, value in defaults.items():
            if getattr(invoice, field_name) != value:
                setattr(invoice, field_name, value)
                changed_fields.append(field_name)
        if changed_fields:
            invoice.save(update_fields=changed_fields)
        return invoice

    @classmethod
    def sync_for_order_id(cls, order_id):
        if not order_id:
            return None
        order = (
            Order.objects.filter(pk=order_id)
            .select_related("user")
            .prefetch_related("items", "payments")
            .first()
        )
        if not order:
            return None
        return cls.sync_for_order(order)

    def save(self, *args, **kwargs):
        if self.order_id:
            if not self.invoice_number:
                self.invoice_number = self.build_invoice_number(self.order_id)
            if self.user_id is None:
                self.user = self.order.user
            self.payment_status = Order.normalize_payment_status(self.payment_status)
        super().save(*args, **kwargs)


class Shipment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=100, blank=True)
    service_level = models.CharField(max_length=100, blank=True)
    shipment_notes = models.TextField(blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment for Order #{self.order_id}"


class DeliveryAgent(models.Model):
    """Represents a member of the in-house delivery team."""

    class VehicleType(models.TextChoices):
        BIKE = "bike", "Bike"
        CAR = "car", "Car"
        VAN = "van", "Van"
        WALK = "walk", "Walking / On Foot"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        default=VehicleType.BIKE,
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def active_assignment_count(self):
        return self.assignments.filter(
            order__order_status__in=[
                Order.OrderStatus.CONFIRMED,
                Order.OrderStatus.PROCESSING,
                Order.OrderStatus.SHIPPED,
            ]
        ).count()


class DeliveryAssignment(models.Model):
    """Links a delivery agent to an order with an ETA and optional notes."""

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery_assignment"
    )
    agent = models.ForeignKey(
        DeliveryAgent,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assignments",
    )
    estimated_delivery = models.DateField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"Assignment: Order #{self.order_id} → {self.agent}"


class Technician(models.Model):
    """Rich profile for a professional installation technician."""
    
    class ExpertiseLevel(models.TextChoices):
        EXPERT = "Expert", "Security Expert"
        SENIOR = "Senior", "Senior Installer"
        LEAD = "Lead", "Lead Systems Engineer"
        SPECIALIST = "Specialist", "Smart Home Specialist"

    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='technicians/', null=True, blank=True)
    phone = models.CharField(max_length=20)
    expertise_level = models.CharField(
        max_length=50,
        choices=ExpertiseLevel.choices,
        default=ExpertiseLevel.EXPERT,
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    is_verified = models.BooleanField(default=True)
    bio = models.TextField(blank=True, help_text="Short professional bio for the customer.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_expertise_level_display()})"


class InstallationBooking(models.Model):
    """Tracks scheduled installation slots for an order."""

    class BookingStatus(models.TextChoices):
        PENDING = "pending", "Pending Confirmation"
        ASSIGNED = "assigned", "Technician Assigned"
        ON_SITE = "on_site", "On-Site / In-Progress"
        COMPLETED = "completed", "Installation Completed"
        CANCELLED = "cancelled", "Cancelled"

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="installation_booking"
    )
    preferred_date = models.DateField()
    preferred_time_slot = models.CharField(max_length=50) # e.g., 'Morning (9 AM - 1 PM)'
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    
    # New: Rich relationship
    technician = models.ForeignKey(
        Technician, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="bookings"
    )
    
    # Legacy fallbacks
    technician_name = models.CharField(max_length=200, blank=True)
    technician_phone = models.CharField(max_length=20, blank=True)
    technician_verified = models.BooleanField(default=False)
    technician_notes = models.TextField(blank=True)
    completion_certificate = models.FileField(upload_to='certificates/%Y/%m/', null=True, blank=True)
    certificate_generated_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["preferred_date"]

    def __str__(self):
        return f"Installation: Order #{self.order_id} on {self.preferred_date}"


class InstallationPhoto(models.Model):
    """Stores visual proof (Before/After) for installations."""

    class PhotoLabel(models.TextChoices):
        BEFORE = "before", "Before Installation"
        DURING = "during", "During Progress"
        AFTER = "after", "After Completion"

    booking = models.ForeignKey(
        InstallationBooking, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="installations/%Y/%m/")
    label = models.CharField(
        max_length=20, choices=PhotoLabel.choices, default=PhotoLabel.DURING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_label_display()} - Order #{self.booking.order_id}"


class ReturnRequest(models.Model):
    class ReturnStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved - Waiting for Pickup"
        PICKED_UP = "picked_up", "Item Picked Up"
        REJECTED = "rejected", "Return Rejected"
        COMPLETED = "completed", "Return Completed & Refunded"

    class ReturnReason(models.TextChoices):
        DEFECTIVE = "defective", "Defective/Not Working"
        WRONG_ITEM = "wrong_item", "Received Wrong Item"
        DAMAGED = "damaged", "Item Damaged on Arrival"
        NOT_AS_DESCRIBED = "not_as_described", "Item Not as Described"
        OTHER = "other", "Other Reason"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="return_requests")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=ReturnReason.choices)
    details = models.TextField(help_text="Detailed description of the issue")
    status = models.CharField(max_length=50, choices=ReturnStatus.choices, default=ReturnStatus.PENDING)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    admin_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return Request - {self.order.formatted_id} - {self.get_status_display()}"

    class Meta:
        ordering = ["-created_at"]


class ReturnItem(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="returned_items")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Return Item: {self.order_item.product.name} (Qty: {self.quantity})"


class ReturnPhoto(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="returns/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
