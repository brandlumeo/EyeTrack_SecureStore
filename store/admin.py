from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'camera_type', 'resolution_mp', 'price', 'stock', 'is_available', 'created_at')
    list_filter = ('is_available', 'created_at', 'category', 'camera_type', 'connectivity', 'ai_detection', 'audio_support')
    search_fields = ('name', 'description', 'weatherproof_rating', 'storage_support')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic', {
            'fields': ('category', 'name', 'slug', 'description', 'image', 'is_available')
        }),
        ('CCTV Technical Specs', {
            'fields': (
                'camera_type', 'resolution_mp', 'lens_mm', 'field_of_view_deg', 'night_vision_range_m',
                'frame_rate_fps', 'weatherproof_rating', 'connectivity', 'power_source',
                'storage_support', 'audio_support', 'ai_detection', 'warranty_years',
            )
        }),
        ('Inventory & Pricing', {
            'fields': ('price', 'stock')
        }),
    )
