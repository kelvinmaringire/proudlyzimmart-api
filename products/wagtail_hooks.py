"""
Wagtail ModelAdmin configuration for products app.
Provides Wagtail admin interface for managing products, categories, and related models.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Category,
    ProductType,
    Product,
    ProductVariation,
    ProductImage,
    Review,
    RelatedProduct,
    ProductVideo,
    ProductBundle,
    BundleItem,
)


class CategoryAdmin(ModelAdmin):
    """Wagtail admin interface for Category model."""
    model = Category
    menu_label = "Categories"
    menu_icon = "folder"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "slug", "parent", "is_active", "order", "product_count", "created_at")
    list_filter = ("is_active", "parent", "created_at")
    search_fields = ("name", "slug", "description")
    ordering = ("order", "name")
    
    def product_count(self, obj):
        """Display count of products in category."""
        return obj.products.filter(is_active=True).count()
    product_count.short_description = "Products"


class ProductTypeAdmin(ModelAdmin):
    """Wagtail admin interface for ProductType model."""
    model = ProductType
    menu_label = "Product Types"
    menu_icon = "tag"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "type", "is_active", "product_count")
    list_filter = ("is_active", "type")
    search_fields = ("name", "type", "description")
    
    def product_count(self, obj):
        """Display count of products of this type."""
        return obj.products.filter(is_active=True).count()
    product_count.short_description = "Products"


class ProductAdmin(ModelAdmin):
    """Wagtail admin interface for Product model."""
    model = Product
    menu_label = "Products"
    menu_icon = "doc-full"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "name", "sku", "brand", "category", "product_type",
        "price_display", "stock_quantity", "in_stock",
        "is_active", "is_featured", "average_rating", "created_at"
    )
    list_filter = (
        "is_active", "is_featured", "is_standard", "is_proudlyzimmart_brand",
        "product_type", "category", "in_stock", "created_at"
    )
    search_fields = ("name", "sku", "brand", "description", "tags")
    ordering = ("-created_at",)
    
    def price_display(self, obj):
        """Display price information."""
        prices = []
        if obj.price_usd:
            sale = f" <span style='color: red;'>Sale: ${obj.sale_price_usd}</span>" if obj.sale_price_usd else ""
            prices.append(f"USD: ${obj.price_usd}{sale}")
        if obj.price_zwl:
            sale = f" <span style='color: red;'>Sale: ZWL {obj.sale_price_zwl}</span>" if obj.sale_price_zwl else ""
            prices.append(f"ZWL: {obj.price_zwl}{sale}")
        if obj.price_zar:
            sale = f" <span style='color: red;'>Sale: ZAR {obj.sale_price_zar}</span>" if obj.sale_price_zar else ""
            prices.append(f"ZAR: {obj.price_zar}{sale}")
        return mark_safe("<br>".join(prices) if prices else "No price set")
    price_display.short_description = "Pricing"


class ProductVariationAdmin(ModelAdmin):
    """Wagtail admin interface for ProductVariation model."""
    model = ProductVariation
    menu_label = "Product Variations"
    menu_icon = "list-ul"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("product", "name", "value", "sku", "stock_quantity", "is_active")
    list_filter = ("is_active", "name", "product")
    search_fields = ("product__name", "name", "value", "sku")


class ProductImageAdmin(ModelAdmin):
    """Wagtail admin interface for ProductImage model."""
    model = ProductImage
    menu_label = "Product Images"
    menu_icon = "image"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("product", "image_preview", "is_primary", "order", "created_at")
    list_filter = ("is_primary", "created_at")
    search_fields = ("product__name", "alt_text")
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


class ReviewAdmin(ModelAdmin):
    """Wagtail admin interface for Review model."""
    model = Review
    menu_label = "Reviews"
    menu_icon = "comment"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "product", "user", "rating", "is_approved", 
        "is_verified_purchase", "helpful_count", "created_at"
    )
    list_filter = ("is_approved", "is_verified_purchase", "rating", "created_at")
    search_fields = ("product__name", "user__username", "title", "comment")


class RelatedProductAdmin(ModelAdmin):
    """Wagtail admin interface for RelatedProduct model."""
    model = RelatedProduct
    menu_label = "Related Products"
    menu_icon = "link"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("product", "related_product", "order")
    list_filter = ("product",)
    search_fields = ("product__name", "related_product__name")


class ProductVideoAdmin(ModelAdmin):
    """Wagtail admin interface for ProductVideo model."""
    model = ProductVideo
    menu_label = "Product Videos"
    menu_icon = "media"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "product", "title", "video_type", "is_primary", 
        "is_active", "order", "created_at"
    )
    list_filter = ("is_active", "is_primary", "video_type", "created_at")
    search_fields = ("product__name", "title", "video_url")


class ProductBundleAdmin(ModelAdmin):
    """Wagtail admin interface for ProductBundle model."""
    model = ProductBundle
    menu_label = "Product Bundles"
    menu_icon = "snippet"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "name", "slug", "bundle_price_display", "discount_percentage",
        "item_count", "is_active", "is_featured", "created_at"
    )
    list_filter = ("is_active", "is_featured", "created_at")
    search_fields = ("name", "slug", "description")
    ordering = ("-created_at",)
    
    def bundle_price_display(self, obj):
        """Display bundle price information."""
        prices = []
        if obj.bundle_price_usd:
            prices.append(f"USD: ${obj.bundle_price_usd}")
        if obj.bundle_price_zwl:
            prices.append(f"ZWL: {obj.bundle_price_zwl}")
        if obj.bundle_price_zar:
            prices.append(f"ZAR: {obj.bundle_price_zar}")
        return mark_safe("<br>".join(prices) if prices else "No price set")
    bundle_price_display.short_description = "Bundle Pricing"
    
    def item_count(self, obj):
        """Display count of items in bundle."""
        return obj.bundle_items.count()
    item_count.short_description = "Items"


class BundleItemAdmin(ModelAdmin):
    """Wagtail admin interface for BundleItem model."""
    model = BundleItem
    menu_label = "Bundle Items"
    menu_icon = "list-ol"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("bundle", "product", "quantity", "order")
    list_filter = ("bundle",)
    search_fields = ("bundle__name", "product__name")


# Group all product models under a single "Products" menu section
class ProductsAdminGroup(ModelAdminGroup):
    menu_label = "Products"  # Main menu label - isolates products app
    menu_icon = "snippet"  # Main menu icon
    menu_order = 200  # Menu order in sidebar
    items = (
        ProductAdmin,
        CategoryAdmin,
        ProductTypeAdmin,
        ProductVariationAdmin,
        ProductImageAdmin,
        ProductVideoAdmin,
        ProductBundleAdmin,
        BundleItemAdmin,
        ReviewAdmin,
        RelatedProductAdmin,
    )


# Register the Products group (this registers all models under one menu section)
modeladmin_register(ProductsAdminGroup)

