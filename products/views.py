"""
API views for products app.
Handles product listing, detail, creation, updates, search, filtering, and reviews.
"""
from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone

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
from .serializers import (
    CategorySerializer,
    ProductTypeSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductVariationSerializer,
    ProductImageSerializer,
    ReviewSerializer,
    RelatedProductSerializer,
    ProductVideoSerializer,
    ProductBundleListSerializer,
    ProductBundleDetailSerializer,
    ProductBundleCreateUpdateSerializer,
    BundleItemSerializer,
)


class CategoryListView(generics.ListAPIView):
    """
    List all active categories.
    
    GET /api/products/categories/
    Returns all active categories with their children.
    """
    queryset = Category.objects.filter(is_active=True, parent=None)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve a category by slug.
    
    GET /api/products/categories/<slug>/
    Returns category details with products.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class ProductTypeListView(generics.ListAPIView):
    """
    List all active product types.
    
    GET /api/products/types/
    Returns all active product types.
    """
    queryset = ProductType.objects.filter(is_active=True)
    serializer_class = ProductTypeSerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model.
    
    Provides CRUD operations and additional actions for products.
    """
    queryset = Product.objects.select_related('category', 'product_type').prefetch_related(
        'images', 'variations', 'reviews'
    )
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'brand', 'sku', 'tags']
    ordering_fields = ['created_at', 'price_usd', 'average_rating', 'name']
    ordering = ['-created_at']
    filterset_fields = {
        'category': ['exact'],
        'product_type': ['exact'],
        'brand': ['exact', 'icontains'],
        'is_active': ['exact'],
        'is_featured': ['exact'],
        'is_proudlyzimmart_brand': ['exact'],
        'in_stock': ['exact'],
        'price_usd': ['gte', 'lte'],
        'average_rating': ['gte'],
    }

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Only show active products for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Filter by category slug
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by product type
        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type__type=product_type)
        
        # Filter by min/max price
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(
                Q(price_usd__gte=min_price) |
                Q(sale_price_usd__gte=min_price)
            )
        if max_price:
            queryset = queryset.filter(
                Q(price_usd__lte=max_price) |
                Q(sale_price_usd__lte=max_price)
            )
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        # Filter by in stock
        in_stock_only = self.request.query_params.get('in_stock_only')
        if in_stock_only and in_stock_only.lower() == 'true':
            queryset = queryset.filter(in_stock=True)
        
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=True, methods=['get'], url_path='variations')
    def variations(self, request, pk=None):
        """Get product variations."""
        product = self.get_object()
        variations = product.variations.filter(is_active=True)
        serializer = ProductVariationSerializer(variations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='images')
    def images(self, request, pk=None):
        """Get product images."""
        product = self.get_object()
        images = product.images.all()
        serializer = ProductImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='videos')
    def videos(self, request, pk=None):
        """Get product videos."""
        product = self.get_object()
        videos = product.videos.filter(is_active=True)
        serializer = ProductVideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='reviews')
    def reviews(self, request, pk=None):
        """Get product reviews."""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        
        # Pagination
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, pk=None):
        """Add a review to a product."""
        product = self.get_object()
        
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(product=product, user=request.user).first()
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        
        # Update product rating
        product.update_rating()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='related')
    def related_products(self, request, pk=None):
        """Get related products."""
        product = self.get_object()
        related = product.related_products.select_related('related_product')[:10]
        serializer = RelatedProductSerializer(related, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        """Get featured products."""
        featured_products = self.get_queryset().filter(is_featured=True)[:20]
        serializer = ProductListSerializer(featured_products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='on-sale')
    def on_sale(self, request):
        """Get products on sale."""
        queryset = self.get_queryset()
        on_sale_products = [
            p for p in queryset if p.is_on_sale()
        ][:20]
        serializer = ProductListSerializer(on_sale_products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Advanced search with auto-suggest."""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})
        
        # Search in multiple fields
        products = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query) |
            Q(tags__icontains=query)
        )[:10]
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response({
            'query': query,
            'results': serializer.data,
            'count': len(serializer.data)
        })


class ProductVariationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductVariation model.
    
    GET /api/products/variations/ - List all variations
    POST /api/products/variations/ - Create variation (admin only)
    """
    queryset = ProductVariation.objects.select_related('product')
    serializer_class = ProductVariationSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_active']


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductImage model.
    
    GET /api/products/images/ - List all images
    POST /api/products/images/ - Upload image (admin only)
    """
    queryset = ProductImage.objects.select_related('product')
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_primary']

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review model.
    
    GET /api/products/reviews/ - List all approved reviews
    POST /api/products/reviews/ - Create review (authenticated users)
    """
    queryset = Review.objects.select_related('product', 'user').filter(is_approved=True)
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    filterset_fields = ['product', 'rating', 'is_verified_purchase']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Create review and update product rating."""
        review = serializer.save()
        review.product.update_rating()

    def perform_update(self, serializer):
        """Update review and product rating."""
        review = serializer.save()
        review.product.update_rating()

    def perform_destroy(self, instance):
        """Delete review and update product rating."""
        product = instance.product
        instance.delete()
        product.update_rating()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        """Mark a review as helpful."""
        review = self.get_object()
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        return Response({'message': 'Review marked as helpful.'})


class RelatedProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RelatedProduct model.
    
    GET /api/products/related/ - List all related products
    POST /api/products/related/ - Create related product (admin only)
    """
    queryset = RelatedProduct.objects.select_related('product', 'related_product')
    serializer_class = RelatedProductSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'related_product']


class ProductSearchView(APIView):
    """
    Advanced product search endpoint.
    
    GET /api/products/search/?q=query&category=slug&min_price=100&max_price=500&rating=4
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Perform advanced product search."""
        query = request.query_params.get('q', '')
        category_slug = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        min_rating = request.query_params.get('min_rating')
        product_type = request.query_params.get('product_type')
        brand = request.query_params.get('brand')
        in_stock_only = request.query_params.get('in_stock_only', 'false').lower() == 'true'
        
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
        
        # Filters
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if product_type:
            queryset = queryset.filter(product_type__type=product_type)
        
        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        
        if min_price:
            queryset = queryset.filter(
                Q(price_usd__gte=min_price) |
                Q(sale_price_usd__gte=min_price)
            )
        
        if max_price:
            queryset = queryset.filter(
                Q(price_usd__lte=max_price) |
                Q(sale_price_usd__lte=max_price)
            )
        
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        if in_stock_only:
            queryset = queryset.filter(in_stock=True)
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        products = queryset[start:end]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'count': queryset.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class ProductVideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductVideo model.
    
    GET /api/products/videos/ - List all videos
    POST /api/products/videos/ - Upload video (admin only)
    """
    queryset = ProductVideo.objects.select_related('product').filter(is_active=True)
    serializer_class = ProductVideoSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'video_type', 'is_primary']

    def get_queryset(self):
        """Filter queryset based on permissions."""
        queryset = super().get_queryset()
        # Allow non-admin users to see active videos
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), permissions.IsAdminUser()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductBundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductBundle model.
    
    GET /api/products/bundles/ - List all bundles
    POST /api/products/bundles/ - Create bundle (admin only)
    """
    queryset = ProductBundle.objects.prefetch_related('bundle_items__product').filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'bundle_price_usd', 'discount_percentage', 'name']
    ordering = ['-created_at']
    filterset_fields = {
        'is_active': ['exact'],
        'is_featured': ['exact'],
        'bundle_price_usd': ['gte', 'lte'],
        'discount_percentage': ['gte'],
    }

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductBundleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductBundleCreateUpdateSerializer
        return ProductBundleDetailSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Only show active bundles for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Filter by featured
        featured_only = self.request.query_params.get('featured_only')
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'], url_path='items')
    def items(self, request, pk=None):
        """Get bundle items."""
        bundle = self.get_object()
        items = bundle.bundle_items.select_related('product').prefetch_related('product__images')
        serializer = BundleItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        """Get featured bundles."""
        featured_bundles = self.get_queryset().filter(is_featured=True)[:20]
        serializer = ProductBundleListSerializer(featured_bundles, many=True, context={'request': request})
        return Response(serializer.data)
