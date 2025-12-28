"""
Service layer for products business logic.
Handles product-related operations and calculations.
"""
from django.db.models import Q, Avg, Count, F
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

