"""
API views for manufacturers app.
Handles manufacturer listing, detail, creation, updates, and related products.
All views use DRF Generic Views following the products app pattern.
"""
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Manufacturer, ManufacturerSubmission
from .serializers import (
    ManufacturerListSerializer,
    ManufacturerDetailSerializer,
    ManufacturerCreateUpdateSerializer,
    ManufacturerSubmissionSerializer,
    ManufacturerSubmissionAdminSerializer,
)
from .services import send_submission_notification_email


class ManufacturerListCreateView(generics.ListCreateAPIView):
    """
    List all manufacturers or create a new manufacturer.
    
    GET /api/manufacturers/ - List manufacturers with filtering
    POST /api/manufacturers/ - Create manufacturer (admin only)
    """
    queryset = Manufacturer.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'city', 'province']
    ordering_fields = ['name', 'created_at', 'product_count']
    ordering = ['name']
    filterset_fields = {
        'is_active': ['exact'],
        'is_verified': ['exact'],
        'is_featured': ['exact'],
        'province': ['exact', 'icontains'],
        'city': ['exact', 'icontains'],
        'country': ['exact'],
    }

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method == 'POST':
            return ManufacturerCreateUpdateSerializer
        return ManufacturerListSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Only show active manufacturers for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Filter by featured
        featured_only = self.request.query_params.get('featured_only')
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter by verified
        verified_only = self.request.query_params.get('verified_only')
        if verified_only and verified_only.lower() == 'true':
            queryset = queryset.filter(is_verified=True)
        
        return queryset

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ManufacturerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a manufacturer.
    
    GET /api/manufacturers/<id>/ - Get manufacturer details
    PUT /api/manufacturers/<id>/ - Update manufacturer (admin only)
    PATCH /api/manufacturers/<id>/ - Partial update (admin only)
    DELETE /api/manufacturers/<id>/ - Delete manufacturer (admin only)
    """
    queryset = Manufacturer.objects.prefetch_related('products__images')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method in ['PUT', 'PATCH']:
            return ManufacturerCreateUpdateSerializer
        return ManufacturerDetailSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Filter queryset based on permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ManufacturerProductsView(APIView):
    """
    Get products from a specific manufacturer.
    
    GET /api/manufacturers/<id>/products/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        manufacturer = get_object_or_404(Manufacturer, pk=pk)
        
        # Check if manufacturer is active (for non-staff users)
        if not request.user.is_staff and not manufacturer.is_active:
            return Response(
                {'error': 'Manufacturer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get products
        products = manufacturer.products.filter(is_active=True).select_related(
            'category', 'product_type'
        ).prefetch_related('images')
        
        # Apply filters
        category_slug = request.query_params.get('category_slug')
        if category_slug:
            products = products.filter(category__slug=category_slug)
        
        product_type = request.query_params.get('product_type')
        if product_type:
            products = products.filter(product_type__type=product_type)
        
        in_stock_only = request.query_params.get('in_stock_only')
        if in_stock_only and in_stock_only.lower() == 'true':
            products = products.filter(in_stock=True)
        
        # Limit results
        limit = int(request.query_params.get('limit', 50))
        products = products[:limit]
        
        # Serialize products (using ProductListSerializer pattern)
        from products.serializers import ProductListSerializer
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'manufacturer': {
                'id': manufacturer.id,
                'name': manufacturer.name,
                'slug': manufacturer.slug,
            },
            'products': serializer.data,
            'count': len(serializer.data),
        })


class ManufacturerFeaturedView(APIView):
    """
    Get featured manufacturers.
    
    GET /api/manufacturers/featured/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        manufacturers = Manufacturer.objects.filter(
            is_featured=True,
            is_active=True
        )[:20]
        serializer = ManufacturerListSerializer(
            manufacturers,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class ManufacturerSearchView(APIView):
    """
    Advanced manufacturer search endpoint.
    
    GET /api/manufacturers/search/?q=query&province=Harare&city=Harare
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Perform advanced manufacturer search."""
        query = request.query_params.get('q', '')
        province = request.query_params.get('province')
        city = request.query_params.get('city')
        verified_only = request.query_params.get('verified_only', 'false').lower() == 'true'
        featured_only = request.query_params.get('featured_only', 'false').lower() == 'true'
        
        queryset = Manufacturer.objects.filter(is_active=True)
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(city__icontains=query) |
                Q(province__icontains=query)
            )
        
        # Filters
        if province:
            queryset = queryset.filter(province__icontains=province)
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        if verified_only:
            queryset = queryset.filter(is_verified=True)
        
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        # Ordering
        ordering = request.query_params.get('ordering', 'name')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        manufacturers = queryset[start:end]
        serializer = ManufacturerListSerializer(
            manufacturers,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': queryset.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


# ==================== Manufacturer Submission Views ====================

class ManufacturerSubmissionCreateView(generics.CreateAPIView):
    """
    Create a new manufacturer submission (public endpoint).
    
    POST /api/manufacturers/submit/
    Submit an application to become a manufacturer/seller on ProudlyZimmart.
    """
    queryset = ManufacturerSubmission.objects.all()
    serializer_class = ManufacturerSubmissionSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create submission and send email notification."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        
        # Send email notification
        try:
            send_submission_notification_email(submission)
        except Exception as e:
            # Log error but don't fail the submission
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send submission notification: {str(e)}")
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Your application has been submitted successfully. We will review it and get back to you soon.',
                'submission': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ManufacturerSubmissionListView(generics.ListAPIView):
    """
    List all manufacturer submissions (admin only).
    
    GET /api/manufacturers/submissions/
    Returns all submissions with filtering options.
    """
    queryset = ManufacturerSubmission.objects.all()
    serializer_class = ManufacturerSubmissionAdminSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'company_name', 'phone']
    ordering_fields = ['created_at', 'status', 'name']
    ordering = ['-created_at']
    filterset_fields = {
        'status': ['exact'],
        'province': ['exact', 'icontains'],
        'city': ['exact', 'icontains'],
        'country': ['exact'],
    }
    
    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ManufacturerSubmissionDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a manufacturer submission (admin only).
    
    GET /api/manufacturers/submissions/<id>/ - Get submission details
    PATCH /api/manufacturers/submissions/<id>/ - Update submission status/notes
    """
    queryset = ManufacturerSubmission.objects.all()
    serializer_class = ManufacturerSubmissionAdminSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Update submission and handle status changes."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Check if status is being changed
        old_status = instance.status
        self.perform_update(serializer)
        new_status = serializer.instance.status
        
        # If status changed from pending, ensure reviewed_by and reviewed_at are set
        if old_status == 'pending' and new_status != 'pending':
            if not serializer.instance.reviewed_by:
                serializer.instance.reviewed_by = request.user
            if not serializer.instance.reviewed_at:
                from django.utils import timezone
                serializer.instance.reviewed_at = timezone.now()
                serializer.instance.save(update_fields=['reviewed_by', 'reviewed_at'])
        
        return Response(serializer.data)
