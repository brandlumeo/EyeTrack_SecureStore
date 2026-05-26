from django.contrib import admin

from .models import Address, Profile, Notification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "email_verified", "updated_at")
    search_fields = ("user__username", "user__email", "phone_number")
    list_filter = ("email_verified",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "state", "country", "is_default")
    search_fields = ("full_name", "user__username", "user__email", "phone_number", "city", "pincode")
    list_filter = ("country", "state", "is_default")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "user__email")
    list_filter = ("notification_type", "is_read", "created_at")
