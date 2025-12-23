from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""
    list_display = ('username', 'email', 'email_verified', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('email_verified', 'is_staff', 'is_active', 'sex')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('email_verified', 'dob', 'sex', 'physical_address', 'phone_number')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'first_name', 'last_name')
        }),
    )
