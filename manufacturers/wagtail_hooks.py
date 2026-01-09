"""
Wagtail ModelAdmin configuration for manufacturers app.
Provides Wagtail admin interface for managing manufacturers with structured panels.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Manufacturer


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


# Register the Manufacturer admin
modeladmin_register(ManufacturerAdmin)

