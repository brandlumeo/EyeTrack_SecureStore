from django.contrib import admin
from .models import (
    Category, Product, CameraSpecification, BiometricSpecification,
    SmartLockSpecification, NetworkDeviceSpecification, Coupon, Review,
    ReviewMedia, ProductGallery, ServiceableArea, StockNotification, ReviewHelpful,
    Project, ProjectImage,
)
from .specs import (
    SPEC_TYPE_BIOMETRIC,
    SPEC_TYPE_CCTV,
    SPEC_TYPE_NETWORK,
    SPEC_TYPE_SMART_LOCK,
    SPEC_TYPE_VIDEO_DOOR_PHONE,
    get_product_spec_type,
)

@admin.register(ServiceableArea)
class ServiceableAreaAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'delivery_available', 'installation_available', 'delivery_charge', 'estimated_delivery_days', 'updated_at')
    list_filter = ('delivery_available', 'installation_available')
    search_fields = ('pincode',)
    ordering = ('pincode',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_to', 'active', 'current_uses', 'max_uses')
    list_filter = ('active', 'valid_from', 'valid_to')
    search_fields = ('code',)
    readonly_fields = ('current_uses',)


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class CameraSpecificationInline(admin.StackedInline):

    model = CameraSpecification
    can_delete = False

class BiometricSpecificationInline(admin.StackedInline):
    model = BiometricSpecification
    can_delete = False

class SmartLockSpecificationInline(admin.StackedInline):
    model = SmartLockSpecification
    can_delete = False

class NetworkDeviceSpecificationInline(admin.StackedInline):
    model = NetworkDeviceSpecification
    can_delete = False

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for managing product categories"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name', 'slug')
    ordering = ('name',)
    
    def product_count(self, obj):
        """Display count of products in each category"""
        count = obj.products.count()
        return f"{count} product{'s' if count != 1 else ''}"
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for managing products with advanced configuration"""
    list_display = ('name', 'category', 'price', 'is_free_shipping', 'stock', 'is_available', 'created_at')
    list_filter = ('is_available', 'created_at', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('📦 Basic Information', {
            'fields': ('category', 'name', 'slug', 'description', 'image', 'is_available'),
            'description': 'Essential product details and categorization'
        }),
        ('💰 Inventory & Pricing', {
            'fields': ('price', 'stock'),
            'description': 'Product pricing and stock information'
        }),
    )
    
    def get_inlines(self, request, obj=None):
        inlines = [ProductGalleryInline]
        if obj and obj.category:
            spec_type = get_product_spec_type(obj)
            if spec_type == SPEC_TYPE_BIOMETRIC:
                inlines.append(BiometricSpecificationInline)
            elif spec_type == SPEC_TYPE_SMART_LOCK:
                inlines.append(SmartLockSpecificationInline)
            elif spec_type == SPEC_TYPE_NETWORK:
                inlines.append(NetworkDeviceSpecificationInline)
        return inlines

    
    def get_readonly_fields(self, request, obj=None):
        """Make created_at and updated_at read-only"""
        if obj:
            return ('created_at', 'updated_at')
        return ()
    
    def get_fieldsets(self, request, obj=None):
        """Show appropriate specification fieldsets based on product category"""
        fieldsets = [
            ('📦 Basic Information', {
                'fields': ('category', 'name', 'slug', 'description', 'image', 'is_available'),
                'description': 'Essential product details and categorization'
            }),
            ('💰 Inventory & Pricing', {
                'fields': ('price', 'stock', 'is_free_shipping'),
                'description': 'Product pricing and stock information'
            }),
        ]
        
        if obj and obj.category:
            spec_type = get_product_spec_type(obj)
            if spec_type == SPEC_TYPE_CCTV:
                fieldsets.append((
                    '📷 CCTV Specifications', {
                        'fields': (
                            'camera_type', 'resolution', 'night_vision_range', 
                            'field_of_view', 'lens', 'frame_rate', 'weatherproof',
                            'connectivity', 'power_source', 'storage_support',
                            'audio_support', 'ai_detection', 'warranty'
                        ),
                        'description': 'CCTV camera technical specifications',
                        'classes': ('collapse',)
                    }
                ))
            elif spec_type == SPEC_TYPE_VIDEO_DOOR_PHONE:
                fieldsets.append((
                    '📞 Video Door Phone Specifications', {
                        'fields': (
                            'screen_size', 'camera_resolution', 'night_vision',
                            'connectivity_type', 'unlock_method', 'audio_communication',
                            'mobile_app_support', 'storage_support_vdp', 'power_source_vdp',
                            'installation_type', 'warranty_vdp'
                        ),
                        'description': 'Video door phone technical specifications',
                        'classes': ('collapse',)
                    }
                ))
        
        return fieldsets

class ReviewMediaInline(admin.TabularInline):
    model = ReviewMedia
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'rating')
    search_fields = ('product__name', 'user__username', 'subject', 'review')
    readonly_fields = ('created_at', 'updated_at', 'ip')
    inlines = [ReviewMediaInline]

@admin.register(ReviewMedia)
class ReviewMediaAdmin(admin.ModelAdmin):
    list_display = ('review', 'is_video', 'created_at')
    list_filter = ('is_video', 'created_at')


@admin.register(StockNotification)
class StockNotificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'product', 'notified', 'created_at')
    list_filter = ('notified', 'created_at')
    search_fields = ('email', 'product__name')
    readonly_fields = ('created_at',)
    actions = ['mark_as_notified']

    def mark_as_notified(self, request, queryset):
        queryset.update(notified=True)
    mark_as_notified.short_description = "Mark selected as notified"


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ('review', 'session_key', 'is_helpful', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    readonly_fields = ('created_at',)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'site_type', 'location', 'is_published', 'is_featured', 'order', 'completed_on')
    list_filter = ('is_published', 'is_featured', 'site_type')
    list_editable = ('is_published', 'is_featured', 'order')
    search_fields = ('title', 'location', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('products',)
    inlines = [ProjectImageInline]
