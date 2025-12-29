"""
API views for products app.
Handles product listing, detail, creation, updates, search, filtering, and reviews.
All views use DRF Generic Views instead of ViewSets.
"""
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

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


# ==================== Category Views ====================

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


# ==================== Product Type Views ====================

class ProductTypeListView(generics.ListAPIView):
    """
    List all active product types.
    
    GET /api/products/types/
    Returns all active product types.
    """
    queryset = ProductType.objects.filter(is_active=True)
    serializer_class = ProductTypeSerializer
    permission_classes = [permissions.AllowAny]


# ==================== Product Views ====================

class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    
    GET /api/products/products/ - List products with filtering
    POST /api/products/products/ - Create product (admin only)
    """
    queryset = Product.objects.select_related('category', 'product_type').prefetch_related(
        'images', 'variations', 'reviews'
    )
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
        """Return appropriate serializer based on method."""
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer

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
        """Set permissions based on method."""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product.
    
    GET /api/products/products/<id>/ - Get product details
    PUT /api/products/products/<id>/ - Update product (admin only)
    PATCH /api/products/products/<id>/ - Partial update (admin only)
    DELETE /api/products/products/<id>/ - Delete product (admin only)
    """
    queryset = Product.objects.select_related('category', 'product_type').prefetch_related(
        'images', 'videos', 'variations', 'reviews', 'related_products'
    )
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductVariationsView(APIView):
    """
    Get product variations.
    
    GET /api/products/products/<id>/variations/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        variations = product.variations.filter(is_active=True)
        serializer = ProductVariationSerializer(variations, many=True)
        return Response(serializer.data)


class ProductImagesView(APIView):
    """
    Get product images.
    
    GET /api/products/products/<id>/images/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        images = product.images.all()
        serializer = ProductImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)


class ProductVideosView(APIView):
    """
    Get product videos.
    
    GET /api/products/products/<id>/videos/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        videos = product.videos.filter(is_active=True)
        serializer = ProductVideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)


class ProductReviewsView(generics.ListAPIView):
    """
    Get product reviews.
    
    GET /api/products/products/<id>/reviews/
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return product.reviews.filter(is_approved=True)

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductAddReviewView(generics.CreateAPIView):
    """
    Add a review to a product.
    
    POST /api/products/products/<id>/add_review/
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs['pk'])

    def create(self, request, *args, **kwargs):
        product = self.get_product()
        
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(product=product, user=request.user).first()
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, user=request.user)
        
        # Update product rating
        product.update_rating()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductRelatedProductsView(APIView):
    """
    Get related products.
    
    GET /api/products/products/<id>/related/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        related = product.related_products.select_related('related_product')[:10]
        serializer = RelatedProductSerializer(related, many=True, context={'request': request})
        return Response(serializer.data)


class ProductFeaturedView(APIView):
    """
    Get featured products.
    
    GET /api/products/products/featured/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related('category', 'product_type').prefetch_related('images')[:20]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductOnSaleView(APIView):
    """
    Get products on sale.
    
    GET /api/products/products/on-sale/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related(
            'category', 'product_type'
        ).prefetch_related('images')
        
        on_sale_products = [p for p in products if p.is_on_sale()][:20]
        serializer = ProductListSerializer(on_sale_products, many=True, context={'request': request})
        return Response(serializer.data)


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


# ==================== Product Variation Views ====================

class ProductVariationListCreateView(generics.ListCreateAPIView):
    """
    List all variations or create a new variation.
    
    GET /api/products/variations/ - List variations (admin only)
    POST /api/products/variations/ - Create variation (admin only)
    """
    queryset = ProductVariation.objects.select_related('product')
    serializer_class = ProductVariationSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_active']


class ProductVariationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a variation.
    
    GET /api/products/variations/<id>/ - Get variation (admin only)
    PUT /api/products/variations/<id>/ - Update variation (admin only)
    PATCH /api/products/variations/<id>/ - Partial update (admin only)
    DELETE /api/products/variations/<id>/ - Delete variation (admin only)
    """
    queryset = ProductVariation.objects.select_related('product')
    serializer_class = ProductVariationSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


# ==================== Product Image Views ====================

class ProductImageListCreateView(generics.ListCreateAPIView):
    """
    List all images or upload a new image.
    
    GET /api/products/images/ - List images (admin only)
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


class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an image.
    
    GET /api/products/images/<id>/ - Get image (admin only)
    PUT /api/products/images/<id>/ - Update image (admin only)
    PATCH /api/products/images/<id>/ - Partial update (admin only)
    DELETE /api/products/images/<id>/ - Delete image (admin only)
    """
    queryset = ProductImage.objects.select_related('product')
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ==================== Product Video Views ====================

class ProductVideoListCreateView(generics.ListCreateAPIView):
    """
    List all videos or create a new video.
    
    GET /api/products/videos/ - List videos
    POST /api/products/videos/ - Create video (admin only)
    """
    queryset = ProductVideo.objects.select_related('product').filter(is_active=True)
    serializer_class = ProductVideoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'video_type', 'is_primary']

    def get_queryset(self):
        """Filter queryset based on permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a video.
    
    GET /api/products/videos/<id>/ - Get video
    PUT /api/products/videos/<id>/ - Update video (admin only)
    PATCH /api/products/videos/<id>/ - Partial update (admin only)
    DELETE /api/products/videos/<id>/ - Delete video (admin only)
    """
    queryset = ProductVideo.objects.select_related('product')
    serializer_class = ProductVideoSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ==================== Review Views ====================

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    List all reviews or create a new review.
    
    GET /api/products/reviews/ - List approved reviews
    POST /api/products/reviews/ - Create review (authenticated users)
    """
    queryset = Review.objects.select_related('product', 'user').filter(is_approved=True)
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    filterset_fields = ['product', 'rating', 'is_verified_purchase']

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Create review and update product rating."""
        review = serializer.save(user=self.request.user)
        review.product.update_rating()

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a review.
    
    GET /api/products/reviews/<id>/ - Get review
    PUT /api/products/reviews/<id>/ - Update review (admin only)
    PATCH /api/products/reviews/<id>/ - Partial update (admin only)
    DELETE /api/products/reviews/<id>/ - Delete review (admin only)
    """
    queryset = Review.objects.select_related('product', 'user')
    serializer_class = ReviewSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        """Update review and product rating."""
        review = serializer.save()
        review.product.update_rating()

    def perform_destroy(self, instance):
        """Delete review and update product rating."""
        product = instance.product
        instance.delete()
        product.update_rating()

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ReviewMarkHelpfulView(APIView):
    """
    Mark a review as helpful.
    
    POST /api/products/reviews/<id>/mark_helpful/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        return Response({'message': 'Review marked as helpful.'})


# ==================== Related Product Views ====================

class RelatedProductListCreateView(generics.ListCreateAPIView):
    """
    List all related products or create a new related product.
    
    GET /api/products/related/ - List related products (admin only)
    POST /api/products/related/ - Create related product (admin only)
    """
    queryset = RelatedProduct.objects.select_related('product', 'related_product')
    serializer_class = RelatedProductSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'related_product']

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class RelatedProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a related product.
    
    GET /api/products/related/<id>/ - Get related product (admin only)
    PUT /api/products/related/<id>/ - Update related product (admin only)
    PATCH /api/products/related/<id>/ - Partial update (admin only)
    DELETE /api/products/related/<id>/ - Delete related product (admin only)
    """
    queryset = RelatedProduct.objects.select_related('product', 'related_product')
    serializer_class = RelatedProductSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ==================== Product Bundle Views ====================

class ProductBundleListCreateView(generics.ListCreateAPIView):
    """
    List all bundles or create a new bundle.
    
    GET /api/products/bundles/ - List bundles
    POST /api/products/bundles/ - Create bundle (admin only)
    """
    queryset = ProductBundle.objects.prefetch_related('bundle_items__product').filter(is_active=True)
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
        """Return appropriate serializer based on method."""
        if self.request.method == 'POST':
            return ProductBundleCreateUpdateSerializer
        return ProductBundleListSerializer

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
        """Set permissions based on method."""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductBundleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a bundle.
    
    GET /api/products/bundles/<id>/ - Get bundle details
    PUT /api/products/bundles/<id>/ - Update bundle (admin only)
    PATCH /api/products/bundles/<id>/ - Partial update (admin only)
    DELETE /api/products/bundles/<id>/ - Delete bundle (admin only)
    """
    queryset = ProductBundle.objects.prefetch_related('bundle_items__product')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method in ['PUT', 'PATCH']:
            return ProductBundleCreateUpdateSerializer
        return ProductBundleDetailSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        """Add request to context for image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductBundleItemsView(APIView):
    """
    Get bundle items.
    
    GET /api/products/bundles/<id>/items/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        bundle = get_object_or_404(ProductBundle, pk=pk)
        items = bundle.bundle_items.select_related('product').prefetch_related('product__images')
        serializer = BundleItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


class ProductBundleFeaturedView(APIView):
    """
    Get featured bundles.
    
    GET /api/products/bundles/featured/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        bundles = ProductBundle.objects.filter(
            is_featured=True,
            is_active=True
        ).prefetch_related('bundle_items__product')[:20]
        serializer = ProductBundleListSerializer(bundles, many=True, context={'request': request})
        return Response(serializer.data)
