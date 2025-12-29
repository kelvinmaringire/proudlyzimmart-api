"""
Import/Export resource classes for Product and Category models.
Handles CSV/Excel import/export with proper foreign key resolution.
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DecimalWidget
from import_export.fields import Field
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Product, Category, ProductType


class CategoryResource(resources.ModelResource):
    """Resource class for Category import/export."""
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Category, field='name'),
    )
    
    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'description', 'parent', 'is_active', 'order'
        )
        import_id_fields = ('slug',)
        export_order = ('name', 'slug', 'description', 'parent', 'is_active', 'order')
        skip_unchanged = True
        report_skipped = True
    
    def before_import_row(self, row, **kwargs):
        """Handle slug generation if not provided."""
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])
    
    def import_row(self, row, instance_loader, *args, **kwargs):
        """Override to handle parent category lookup by name."""
        # Extract dry_run from kwargs or args
        dry_run = kwargs.get('dry_run', False)
        if not dry_run and len(args) > 1:
            dry_run = args[1]
        
        # Handle parent category lookup
        if row.get('parent'):
            parent_name = row['parent']
            try:
                parent = Category.objects.get(name=parent_name)
                row['parent'] = parent.pk
            except Category.DoesNotExist:
                if not dry_run:
                    raise ValidationError(f"Parent category '{parent_name}' not found. Please create it first or use an existing category name.")
                row['parent'] = None
        
        return super().import_row(row, instance_loader, *args, **kwargs)


class ProductResource(resources.ModelResource):
    """Resource class for Product import/export."""
    # Foreign key fields with custom widgets
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name'),
    )
    
    product_type = fields.Field(
        column_name='product_type',
        attribute='product_type',
        widget=ForeignKeyWidget(ProductType, field='type'),
    )
    
    # Price fields
    price_usd = Field(attribute='price_usd', column_name='price_usd', widget=DecimalWidget())
    price_zwl = Field(attribute='price_zwl', column_name='price_zwl', widget=DecimalWidget())
    price_zar = Field(attribute='price_zar', column_name='price_zar', widget=DecimalWidget())
    sale_price_usd = Field(attribute='sale_price_usd', column_name='sale_price_usd', widget=DecimalWidget())
    sale_price_zwl = Field(attribute='sale_price_zwl', column_name='sale_price_zwl', widget=DecimalWidget())
    sale_price_zar = Field(attribute='sale_price_zar', column_name='sale_price_zar', widget=DecimalWidget())
    
    class Meta:
        model = Product
        fields = (
            'sku', 'name', 'slug', 'description', 'short_description',
            'category', 'product_type', 'brand', 'manufacturer',
            'is_proudlyzimmart_brand', 'price_usd', 'price_zwl', 'price_zar',
            'sale_price_usd', 'sale_price_zwl', 'sale_price_zar',
            'stock_quantity', 'low_stock_threshold', 'track_stock',
            'in_stock', 'is_active', 'is_featured', 'is_standard',
            'weight', 'dimensions', 'meta_title', 'meta_description', 'tags'
        )
        import_id_fields = ('sku',)  # Use SKU as unique identifier
        export_order = (
            'sku', 'name', 'slug', 'description', 'short_description',
            'category', 'product_type', 'brand', 'manufacturer',
            'is_proudlyzimmart_brand', 'price_usd', 'price_zwl', 'price_zar',
            'sale_price_usd', 'sale_price_zwl', 'sale_price_zar',
            'stock_quantity', 'low_stock_threshold', 'track_stock',
            'in_stock', 'is_active', 'is_featured', 'is_standard',
            'weight', 'dimensions', 'meta_title', 'meta_description', 'tags'
        )
        skip_unchanged = True
        report_skipped = True
    
    def before_import_row(self, row, **kwargs):
        """Handle slug generation and validation before import."""
        # Auto-generate slug if not provided
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])
        
        # Ensure SKU is provided
        if not row.get('sku') and row.get('name'):
            # Generate SKU from name if not provided
            base_sku = slugify(row['name']).upper()[:10]
            row['sku'] = base_sku
    
    def import_row(self, row, instance_loader, *args, **kwargs):
        """Override to handle foreign key lookups."""
        # Extract dry_run from kwargs or args
        dry_run = kwargs.get('dry_run', False)
        if not dry_run and len(args) > 1:
            dry_run = args[1]
        
        # Handle category lookup by name
        if row.get('category'):
            category_name = row['category']
            try:
                category = Category.objects.get(name=category_name)
                row['category'] = category.pk
            except Category.DoesNotExist:
                if not dry_run:
                    raise ValidationError(
                        f"Category '{category_name}' not found for product '{row.get('name', 'Unknown')}'. "
                        f"Please create the category first or use an existing category name."
                    )
                row['category'] = None
        
        # Handle product_type lookup by type field
        if row.get('product_type'):
            product_type_value = row['product_type']
            try:
                # Try to get by 'type' field first (e.g., 'ready_to_buy')
                product_type = ProductType.objects.get(type=product_type_value)
            except ProductType.DoesNotExist:
                try:
                    # Fallback to name field
                    product_type = ProductType.objects.get(name=product_type_value)
                except ProductType.DoesNotExist:
                    if not dry_run:
                        raise ValidationError(
                            f"Product type '{product_type_value}' not found for product '{row.get('name', 'Unknown')}'. "
                            f"Available types: {', '.join([pt.type for pt in ProductType.objects.all()])}"
                        )
                    row['product_type'] = None
                    return None
            
            row['product_type'] = product_type.pk
        
        # Handle boolean fields
        boolean_fields = [
            'is_proudlyzimmart_brand', 'track_stock', 'in_stock',
            'is_active', 'is_featured', 'is_standard'
        ]
        for field in boolean_fields:
            if field in row:
                value = row[field]
                if isinstance(value, str):
                    row[field] = value.lower() in ('true', '1', 'yes', 'on')
                elif value is None:
                    row[field] = False
        
        return super().import_row(row, instance_loader, *args, **kwargs)
    
    def get_export_headers(self, fields=None):
        """Customize export headers for better readability."""
        headers = []
        export_fields = fields if fields is not None else self.get_export_fields()
        for field in export_fields:
            # Convert field names to more readable format
            if hasattr(field, 'column_name'):
                header = field.column_name.replace('_', ' ').title()
            else:
                header = str(field).replace('_', ' ').title()
            headers.append(header)
        return headers

