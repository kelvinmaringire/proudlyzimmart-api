"""
Wagtail ModelAdmin configuration for blog app.
Provides Wagtail admin interface for managing blog posts.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from django.utils.html import format_html
from .models import BlogPost


class BlogPostAdmin(ModelAdmin):
    """Wagtail admin interface for BlogPost model."""
    model = BlogPost
    menu_label = "Blog Posts"
    menu_icon = "doc-full"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "title", "featured_image_preview", "author", "is_published",
        "published_date", "view_count", "created_at"
    )
    list_filter = (
        "is_published", "author", "published_date", "created_at"
    )
    search_fields = ("title", "excerpt", "content", "author__username", "author__email")
    ordering = ("-published_date", "-created_at")
    
    def featured_image_preview(self, obj):
        """Display featured image preview."""
        if obj.featured_image and obj.featured_image.file:
            return format_html(
                '<img src="{}" width="100" height="60" style="object-fit: cover; border-radius: 4px;" />',
                obj.featured_image.file.url
            )
        return "No image"
    featured_image_preview.short_description = "Featured Image"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('author', 'featured_image')


# Register the BlogPost model
modeladmin_register(BlogPostAdmin)

