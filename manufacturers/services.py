"""
Service layer for manufacturers business logic.
Handles manufacturer-related operations and queries.
"""
import os
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from .models import Manufacturer, ManufacturerSubmission


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


def send_submission_notification_email(submission):
    """
    Send email notification to admin when a manufacturer submission is created.
    
    Args:
        submission: ManufacturerSubmission instance
    
    Returns:
        Number of emails sent (0 or 1)
    """
    # Get admin email from environment or use EMAIL_HOST_USER
    admin_email = os.getenv('ADMIN_EMAIL', settings.EMAIL_HOST_USER)
    
    if not admin_email:
        # Fallback to DEFAULT_FROM_EMAIL if ADMIN_EMAIL and EMAIL_HOST_USER are not set
        admin_email = settings.DEFAULT_FROM_EMAIL
    
    if not admin_email:
        # If still no email, log warning and return
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("No admin email configured. Cannot send submission notification.")
        return 0
    
    # Prepare email subject
    company_name = submission.company_name or "No Company Name"
    subject = f"New Manufacturer Application - {company_name}"
    
    # Prepare email body
    body = f"""
New Manufacturer Application Received

Contact Information:
- Name: {submission.name}
- Email: {submission.email}
- Phone: {submission.phone}

Company Details:
- Company Name: {submission.company_name or 'Not provided'}
- Website: {submission.website or 'Not provided'}
- Description: {submission.description or 'Not provided'}

Location:
- City: {submission.city or 'Not provided'}
- Province: {submission.province or 'Not provided'}
- Country: {submission.country}

Product Information:
- Product Types: {submission.product_types or 'Not provided'}
- Product Categories: {submission.product_categories or 'Not provided'}

Submitted: {submission.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Status: {submission.get_status_display()}

---
This is an automated notification from ProudlyZimmart.
Please review this submission in the admin dashboard.
"""
    
    try:
        # Send email
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        return 1
    except Exception as e:
        # Log error but don't fail the submission
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send submission notification email: {str(e)}")
        return 0

