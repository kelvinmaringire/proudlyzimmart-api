"""
Service layer for manufacturers business logic.
Handles manufacturer-related operations and queries.
"""
from django.db.models import Q, Count
from .models import Manufacturer


def get_featured_manufacturers(limit=20):
    """
    Get featured manufacturers.
    
    Args:
        limit: Maximum number of manufacturers to return
    
    Returns:
        QuerySet of featured manufacturers
    """
    return Manufacturer.objects.filter(
        is_featured=True,
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:limit]


def get_manufacturer_products(manufacturer_id, limit=50):
    """
    Get products from a specific manufacturer.
    
    Args:
        manufacturer_id: Manufacturer ID
        limit: Maximum number of products to return
    
    Returns:
        QuerySet of products from the manufacturer
    """
    try:
        manufacturer = Manufacturer.objects.get(id=manufacturer_id, is_active=True)
        return manufacturer.products.filter(
            is_active=True
        ).select_related('category', 'product_type').prefetch_related('images')[:limit]
    except Manufacturer.DoesNotExist:
        return Manufacturer.objects.none()


def get_manufacturers_by_location(province=None, city=None, limit=50):
    """
    Get manufacturers filtered by location.
    
    Args:
        province: Province name (optional)
        city: City name (optional)
        limit: Maximum number of manufacturers to return
    
    Returns:
        QuerySet of manufacturers matching location criteria
    """
    queryset = Manufacturer.objects.filter(is_active=True)
    
    if province:
        queryset = queryset.filter(province__icontains=province)
    
    if city:
        queryset = queryset.filter(city__icontains=city)
    
    return queryset.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:limit]


def search_manufacturers(query, filters=None):
    """
    Search manufacturers with advanced filtering.
    
    Args:
        query: Search query string
        filters: Dictionary of filters (province, city, verified, featured, etc.)
    
    Returns:
        QuerySet of matching manufacturers
    """
    queryset = Manufacturer.objects.filter(is_active=True)
    
    # Text search
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(province__icontains=query)
        )
    
    # Apply filters
    if filters:
        if filters.get('province'):
            queryset = queryset.filter(province__icontains=filters['province'])
        
        if filters.get('city'):
            queryset = queryset.filter(city__icontains=filters['city'])
        
        if filters.get('country'):
            queryset = queryset.filter(country__iexact=filters['country'])
        
        if filters.get('verified_only'):
            queryset = queryset.filter(is_verified=True)
        
        if filters.get('featured_only'):
            queryset = queryset.filter(is_featured=True)
    
    # Annotate with product count
    queryset = queryset.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    return queryset


def get_verified_manufacturers(limit=50):
    """
    Get verified manufacturers.
    
    Args:
        limit: Maximum number of manufacturers to return
    
    Returns:
        QuerySet of verified manufacturers
    """
    return Manufacturer.objects.filter(
        is_verified=True,
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:limit]


def get_manufacturers_with_products(min_product_count=1, limit=50):
    """
    Get manufacturers that have at least a minimum number of products.
    
    Args:
        min_product_count: Minimum number of products required
        limit: Maximum number of manufacturers to return
    
    Returns:
        QuerySet of manufacturers with products
    """
    return Manufacturer.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(
        product_count__gte=min_product_count
    )[:limit]

