"""
Service layer for products business logic.
Handles product-related operations and calculations.
"""
from django.db.models import Q, Avg, Count, F
from django.core.exceptions import ValidationError
from import_export.formats.base_formats import CSV, XLSX
from .models import Product, Category, Review


def calculate_product_rating(product):
    """
    Calculate and update product average rating.
    
    Args:
        product: Product instance
    """
    reviews = Review.objects.filter(product=product, is_approved=True)
    if reviews.exists():
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0.00
        review_count = reviews.count()
    else:
        avg_rating = 0.00
        review_count = 0
    
    product.average_rating = avg_rating
    product.review_count = review_count
    product.save(update_fields=['average_rating', 'review_count'])
    return avg_rating, review_count


def get_products_by_category(category_slug, limit=20):
    """
    Get products by category slug.
    
    Args:
        category_slug: Category slug
        limit: Maximum number of products to return
    
    Returns:
        QuerySet of products
    """
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
        return Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category', 'product_type').prefetch_related('images')[:limit]
    except Category.DoesNotExist:
        return Product.objects.none()


def get_featured_products(limit=20):
    """
    Get featured products.
    
    Args:
        limit: Maximum number of products to return
    
    Returns:
        QuerySet of featured products
    """
    return Product.objects.filter(
        is_featured=True,
        is_active=True
    ).select_related('category', 'product_type').prefetch_related('images')[:limit]


def get_products_on_sale(limit=20):
    """
    Get products currently on sale.
    
    Args:
        limit: Maximum number of products to return
    
    Returns:
        List of products on sale
    """
    products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'product_type').prefetch_related('images')
    
    on_sale = [p for p in products if p.is_on_sale()]
    return on_sale[:limit]


def search_products(query, filters=None):
    """
    Search products with advanced filtering.
    
    Args:
        query: Search query string
        filters: Dictionary of filters (category, min_price, max_price, etc.)
    
    Returns:
        QuerySet of matching products
    """
    queryset = Product.objects.filter(is_active=True).select_related(
        'category', 'product_type'
    ).prefetch_related('images')
    
    # Text search
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query) |
            Q(tags__icontains=query)
        )
    
    # Apply filters
    if filters:
        if filters.get('category'):
            queryset = queryset.filter(category__slug=filters['category'])
        
        if filters.get('product_type'):
            queryset = queryset.filter(product_type__type=filters['product_type'])
        
        if filters.get('min_price'):
            queryset = queryset.filter(
                Q(price_usd__gte=filters['min_price']) |
                Q(sale_price_usd__gte=filters['min_price'])
            )
        
        if filters.get('max_price'):
            queryset = queryset.filter(
                Q(price_usd__lte=filters['max_price']) |
                Q(sale_price_usd__lte=filters['max_price'])
            )
        
        if filters.get('min_rating'):
            queryset = queryset.filter(average_rating__gte=filters['min_rating'])
        
        if filters.get('in_stock_only'):
            queryset = queryset.filter(in_stock=True)
    
    return queryset


def get_low_stock_products(threshold=None):
    """
    Get products with low stock.
    
    Args:
        threshold: Optional threshold (uses product's low_stock_threshold if not provided)
    
    Returns:
        QuerySet of products with low stock
    """
    queryset = Product.objects.filter(
        is_active=True,
        track_stock=True
    )
    
    if threshold:
        queryset = queryset.filter(stock_quantity__lte=threshold)
    else:
        queryset = queryset.filter(
            stock_quantity__lte=F('low_stock_threshold')
        )
    
    return queryset.select_related('category', 'product_type')


# ==================== Import/Export Services ====================

def get_format_instance(file_format):
    """Get format instance for import/export."""
    format_map = {
        'csv': CSV(),
        'xlsx': XLSX(),
    }
    return format_map.get(file_format)


def read_file_content(file, file_format):
    """Read and prepare file content based on format."""
    file.seek(0)
    if file_format == 'csv':
        file_content = file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
        return file_content
    else:
        return file.read()


def extract_import_errors(result):
    """Extract error messages from import result object."""
    error_messages = []
    
    # Check invalid_rows (newer versions)
    if hasattr(result, 'invalid_rows') and result.invalid_rows:
        for row_result in result.invalid_rows:
            error_msg = getattr(row_result, 'error', str(row_result))
            row_num = getattr(row_result, 'number', getattr(row_result, 'row', 'Unknown'))
            error_messages.append(f"Row {row_num}: {error_msg}")
    
    # Check row_errors - might be a method or attribute
    if hasattr(result, 'row_errors'):
        row_errors = result.row_errors
        if callable(row_errors):
            try:
                row_errors = row_errors()
            except Exception:
                pass
        if row_errors and hasattr(row_errors, 'items'):
            try:
                for row_num, errors in row_errors.items():
                    if isinstance(errors, (list, tuple)):
                        for error in errors:
                            error_messages.append(f"Row {row_num}: {error}")
                    else:
                        error_messages.append(f"Row {row_num}: {errors}")
            except Exception:
                pass
    
    # Check diff for errors (contains row-level error information)
    if hasattr(result, 'diff') and result.diff:
        for row_num, row_diff in enumerate(result.diff, start=1):
            if hasattr(row_diff, 'errors') and row_diff.errors:
                if isinstance(row_diff.errors, (list, tuple)):
                    for error in row_diff.errors:
                        error_messages.append(f"Row {row_num}: {error}")
                else:
                    error_messages.append(f"Row {row_num}: {row_diff.errors}")
            elif hasattr(row_diff, 'error') and row_diff.error:
                error_messages.append(f"Row {row_num}: {row_diff.error}")
            elif hasattr(row_diff, 'import_type') and row_diff.import_type == 'error':
                error_msg = getattr(row_diff, 'errors', getattr(row_diff, 'error', 'Unknown error'))
                error_messages.append(f"Row {row_num}: {error_msg}")
            elif hasattr(row_diff, 'diff') and row_diff.diff:
                for field, diff_value in row_diff.diff.items():
                    if isinstance(diff_value, dict) and 'error' in diff_value:
                        error_messages.append(f"Row {row_num}, Field {field}: {diff_value['error']}")
    
    return error_messages


def process_import_result(result):
    """Process import result and return status information."""
    error_messages = extract_import_errors(result)
    
    # Check has_errors() method
    has_errors_flag = False
    if hasattr(result, 'has_errors') and callable(result.has_errors):
        has_errors_flag = result.has_errors()
    
    # If has_errors is True but we haven't found specific errors, check totals
    if has_errors_flag and not error_messages:
        if hasattr(result, 'totals'):
            totals = result.totals
            error_count = totals.get('error', totals.get('invalid', totals.get('skip', 0)))
            if error_count > 0:
                error_messages.append(
                    f"Import completed with {error_count} error(s). "
                    f"Some rows may have been skipped due to validation errors."
                )
            else:
                error_messages.append("Import completed with warnings. Please review the imported data.")
    
    # Get totals
    totals = result.totals if hasattr(result, 'totals') else {}
    
    return {
        'error_messages': error_messages,
        'has_errors': bool(error_messages),
        'totals': totals,
    }


def import_data(resource_class, file, file_format):
    """Import data from file using resource class."""
    format_instance = get_format_instance(file_format)
    if not format_instance:
        raise ValidationError(f"Unsupported file format: {file_format}")
    
    file_content = read_file_content(file, file_format)
    dataset = format_instance.create_dataset(file_content)
    
    resource = resource_class()
    result = resource.import_data(dataset, dry_run=False, raise_errors=False)
    
    return result


def export_data(resource_class, queryset, file_format='csv'):
    """Export data to file format using resource class."""
    format_instance = get_format_instance(file_format) or CSV()
    
    resource = resource_class()
    dataset = resource.export(queryset)
    
    return {
        'data': format_instance.export_data(dataset),
        'content_type': format_instance.get_content_type(),
        'extension': format_instance.get_extension(),
    }
