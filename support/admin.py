from django.contrib import admin
from .models import FAQCategory, FAQ, QuoteRequest, ServiceTicket, TicketAttachment, TicketMessage

@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('is_active', 'order')


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'site_type', 'camera_count', 'location', 'status', 'created_at')
    list_filter = ('status', 'site_type', 'camera_count')
    search_fields = ('name', 'phone', 'email', 'location', 'pincode')
    list_editable = ('status',)


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    fields = ("created_at", "from_staff", "author", "body")
    readonly_fields = ("created_at",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "subject", "user", "category", "status", "priority", "assigned_technician", "updated_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("subject", "description", "user__email", "user__first_name", "contact_phone")
    raw_id_fields = ("user", "order")
    inlines = [TicketMessageInline, TicketAttachmentInline]
