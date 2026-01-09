"""
Wagtail ModelAdmin configuration for manufacturers app.
Provides Wagtail admin interface for managing manufacturers with structured panels.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Manufacturer, ManufacturerSubmission


class ManufacturerAdmin(ModelAdmin):
    """Wagtail admin interface for Manufacturer model."""
    model = Manufacturer
    menu_label = "Manufacturers"
    menu_icon = "group"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "name", "logo_preview", "city", "province", "country",
        "is_active", "is_verified", "is_featured", "product_count", "created_at"
    )
    list_filter = (
        "is_active", "is_verified", "is_featured",
        "province", "city", "country", "created_at"
    )
    search_fields = ("name", "description", "email", "phone", "city", "province")
    ordering = ("name",)
    
    def logo_preview(self, obj):
        """Display logo preview."""
        if obj.logo and obj.logo.file:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.logo.file.url
            )
        return "No logo"
    logo_preview.short_description = "Logo"
    
    def product_count(self, obj):
        """Display count of products from this manufacturer."""
        count = obj.get_product_count()
        if count > 0:
            return format_html(
                '<a href="/admin/products/product/?manufacturer__id__exact={}">{}</a>',
                obj.id,
                count
            )
        return "0"
    product_count.short_description = "Products"


class ManufacturerSubmissionAdmin(ModelAdmin):
    """Wagtail admin interface for ManufacturerSubmission model."""
    model = ManufacturerSubmission
    menu_label = "Form Submissions"
    menu_icon = "form"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "name", "company_name", "email", "phone",
        "status", "province", "city", "created_at"
    )
    list_filter = (
        "status", "province", "city", "country", "created_at"
    )
    search_fields = ("name", "email", "company_name", "phone", "description")
    ordering = ("-created_at",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('reviewed_by')


# Group Manufacturers and Submissions under a single menu section
class ManufacturersAdminGroup(ModelAdminGroup):
    menu_label = "Manufacturers"  # Main menu label
    menu_icon = "group"  # Main menu icon
    menu_order = 210  # Menu order in sidebar (after Products)
    items = (
        ManufacturerAdmin,
        ManufacturerSubmissionAdmin,
    )


# Register the Manufacturers group (this registers all models under one menu section)
modeladmin_register(ManufacturersAdminGroup)

