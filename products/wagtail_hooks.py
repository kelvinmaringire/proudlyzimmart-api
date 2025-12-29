"""
Wagtail ModelAdmin configuration for products app.
Provides Wagtail admin interface for managing products, categories, and related models.
Includes import/export functionality via django-import-export.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from wagtail_modeladmin.views import IndexView
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from import_export.formats.base_formats import CSV, XLSX
from import_export import fields
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
from .resources import ProductResource, CategoryResource


class CategoryImportExportMixin:
    """Mixin to add import/export functionality to ModelAdmin."""
    
    def get_admin_urls_for_registration(self):
        """Add import/export URLs."""
        urls = super().get_admin_urls_for_registration()
        # Store reference to self for closure
        model_admin_instance = self
        
        # Create wrapper functions that capture self in closure
        def import_view_wrapper(request, *args, **kwargs):
            return model_admin_instance.import_view(request)
        
        def export_view_wrapper(request, *args, **kwargs):
            return model_admin_instance.export_view(request)
        
        # Use simple URL patterns that match the index URL structure
        # Convert to list, extend, then convert back to tuple
        urls_list = list(urls) if isinstance(urls, tuple) else list(urls)
        urls_list.extend([
            path('import/', import_view_wrapper, name='import'),
            path('export/', export_view_wrapper, name='export'),
        ])
        return tuple(urls_list)
    
    def import_view(self, request):
        """Handle import view."""
        resource_class = getattr(self, 'import_export_resource', None)
        if not resource_class:
            messages.error(request, "Import/Export not configured for this model.")
            return redirect(self.url_helper.index_url)
        
        if request.method == 'POST':
            file_format = request.POST.get('file_format', 'csv')
            file = request.FILES.get('import_file')
            
            if not file:
                messages.error(request, "Please select a file to import.")
                return render(request, 'products/admin/import.html', {
                    'model_admin': self,
                    'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
                })
            
            # Get format class
            format_map = {
                'csv': CSV(),
                'xlsx': XLSX(),
            }
            format_instance = format_map.get(file_format)
            
            if not format_instance:
                messages.error(request, f"Unsupported file format: {file_format}")
                return render(request, 'products/admin/import.html', {
                    'model_admin': self,
                    'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
                })
            
            try:
                # Read file - django-import-export handles encoding automatically
                file.seek(0)  # Reset file pointer in case it was read before
                dataset = format_instance.create_dataset(file)
                
                # Import data
                resource = resource_class()
                result = resource.import_data(dataset, dry_run=False, raise_errors=False)
                
                # Report results
                if result.has_errors():
                    error_messages = []
                    for error in result.errors:
                        error_messages.append(f"Row {error.row}: {error.error}")
                    messages.error(request, f"Import completed with errors:\n" + "\n".join(error_messages[:10]))
                else:
                    messages.success(
                        request,
                        f"Successfully imported {result.totals['new']} new, "
                        f"{result.totals['update']} updated, "
                        f"{result.totals['skip']} skipped records."
                    )
                
            except Exception as e:
                messages.error(request, f"Error importing file: {str(e)}")
            
            return redirect(self.url_helper.index_url)
        
        return render(request, 'products/admin/import.html', {
            'model_admin': self,
            'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
        })
    
    def export_view(self, request):
        """Handle export view."""
        resource_class = getattr(self, 'import_export_resource', None)
        if not resource_class:
            messages.error(request, "Import/Export not configured for this model.")
            return redirect(self.url_helper.index_url)
        
        file_format = request.GET.get('format', 'csv')
        
        # Get format class
        format_map = {
            'csv': CSV(),
            'xlsx': XLSX(),
        }
        format_instance = format_map.get(file_format, CSV())
        
        # Export data
        resource = resource_class()
        queryset = self.model.objects.all()
        dataset = resource.export(queryset)
        
        # Create response
        response = HttpResponse(
            format_instance.export_data(dataset),
            content_type=format_instance.get_content_type()
        )
        response['Content-Disposition'] = f'attachment; filename="{self.model.__name__.lower()}_export.{format_instance.get_extension()}"'
        
        return response


class CategoryIndexView(IndexView):
    """Custom index view with import/export buttons."""
    
    def get_template_names(self):
        """Override to use custom template."""
        return ['wagtail_modeladmin/products/categoryadmin/index.html', 'modeladmin/index.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_import_export'] = True
        # Construct URLs manually
        base_url = self.model_admin.url_helper.index_url
        context['import_url'] = base_url.rstrip('/') + '/import/'
        context['export_csv_url'] = base_url.rstrip('/') + '/export/?format=csv'
        context['export_xlsx_url'] = base_url.rstrip('/') + '/export/?format=xlsx'
        return context


class CategoryAdmin(CategoryImportExportMixin, ModelAdmin):
    """Wagtail admin interface for Category model with import/export."""
    model = Category
    menu_label = "Categories"
    menu_icon = "folder"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "slug", "parent", "is_active", "order", "product_count", "created_at")
    list_filter = ("is_active", "parent", "created_at")
    search_fields = ("name", "slug", "description")
    ordering = ("order", "name")
    index_view_class = CategoryIndexView
    import_export_resource = CategoryResource
    
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


class ProductIndexView(IndexView):
    """Custom index view with import/export buttons."""
    
    def get_template_names(self):
        """Override to use custom template."""
        return ['wagtail_modeladmin/products/productadmin/index.html', 'modeladmin/index.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_import_export'] = True
        # Construct URLs manually
        base_url = self.model_admin.url_helper.index_url
        context['import_url'] = base_url.rstrip('/') + '/import/'
        context['export_csv_url'] = base_url.rstrip('/') + '/export/?format=csv'
        context['export_xlsx_url'] = base_url.rstrip('/') + '/export/?format=xlsx'
        return context


class ProductAdmin(CategoryImportExportMixin, ModelAdmin):
    """Wagtail admin interface for Product model with import/export."""
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
    index_view_class = ProductIndexView
    import_export_resource = ProductResource
    
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

