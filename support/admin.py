from django.contrib import admin
from .models import FAQCategory, FAQ, QuoteRequest

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
