from django.contrib import admin
from .models import Invoice, Order, OrderItem, Payment, Shipment, DeliveryAgent, DeliveryAssignment, InstallationBooking, InstallationPhoto, Technician


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at', 'paid_at']


class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 1
    max_num = 1
    readonly_fields = ['created_at']


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'order_status',
        'payment_method',
        'payment_status',
        'coupon',
        'discount_amount',
        'total',
        'shipping_status',
        'created_at',
    ]
    list_filter = ['order_status', 'payment_method', 'payment_status', 'shipping_status', 'created_at']
    search_fields = ['=id', 'tracking_number', 'user__email', 'full_name', 'email', 'phone']
    list_editable = ['order_status', 'payment_status', 'shipping_status']
    list_select_related = ['user']
    inlines = [OrderItemInline, PaymentInline, ShipmentInline]


admin.site.register(Order, OrderAdmin)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'payment_method', 'transaction_id', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'order__full_name', 'order__email']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'carrier', 'service_level', 'shipped_at', 'delivered_at', 'created_at']
    list_filter = ['carrier', 'created_at', 'shipped_at', 'delivered_at']
    search_fields = ['order__full_name', 'order__email', 'order__tracking_number', 'carrier']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order', 'user', 'subtotal', 'tax', 'shipping_cost', 'total_amount', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['invoice_number', 'order__id', 'order__tracking_number', 'user__email', 'order__full_name']
    list_select_related = ['order', 'user']


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'vehicle_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'vehicle_type']
    search_fields = ['name', 'phone']
    list_editable = ['is_active']


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'agent', 'estimated_delivery', 'assigned_at', 'completed_at']
    list_filter = ['agent', 'estimated_delivery']
    search_fields = ['order__full_name', 'agent__name']
    autocomplete_fields = ['agent']


class InstallationPhotoInline(admin.TabularInline):
    model = InstallationPhoto
    extra = 1


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'expertise_level', 'phone', 'rating', 'is_verified', 'is_active']
    list_filter = ['expertise_level', 'is_verified', 'is_active']
    search_fields = ['name', 'phone']
    list_editable = ['is_active', 'is_verified']


@admin.register(InstallationBooking)
class InstallationBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'status', 'preferred_date', 'technician', 'technician_name', 'technician_verified']
    list_filter = ['status', 'preferred_date', 'technician_verified']
    search_fields = ['order__id', 'technician_name', 'order__full_name', 'technician__name']
    inlines = [InstallationPhotoInline]
    autocomplete_fields = ['technician']


@admin.register(InstallationPhoto)
class InstallationPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'label', 'uploaded_at']
    list_filter = ['label', 'uploaded_at']
