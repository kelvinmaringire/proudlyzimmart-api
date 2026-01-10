"""
API views for blog app.
Handles blog post listing, detail, creation, updates, and view count tracking.
All views use DRF Generic Views following the manufacturers/products app pattern.
"""
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import BlogPost
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer,
)


class BlogPostListCreateView(generics.ListCreateAPIView):
    """
    List all blog posts or create a new blog post.
    
    GET /api/blog/ - List blog posts with filtering
    POST /api/blog/ - Create blog post (admin only)
    """
    queryset = BlogPost.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_date', 'created_at', 'view_count', 'title']
    ordering = ['-published_date', '-created_at']
    filterset_fields = {
        'is_published': ['exact'],
        'author': ['exact'],
        'published_date': ['exact', 'gte', 'lte', 'gt', 'lt'],
        'created_at': ['exact', 'gte', 'lte', 'gt', 'lt'],
    }

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method == 'POST':
            return BlogPostCreateUpdateSerializer
        return BlogPostListSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters and permissions."""
        queryset = super().get_queryset().select_related('author', 'featured_image')
        
        # Only show published posts for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        # Filter by author username
        author_username = self.request.query_params.get('author_username')
        if author_username:
            queryset = queryset.filter(author__username=author_username)
        
        # Filter by published only
        published_only = self.request.query_params.get('published_only')
        if published_only and published_only.lower() == 'true':
            queryset = queryset.filter(is_published=True)
        
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


class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a blog post.
    
    GET /api/blog/<id>/ - Get blog post details
    PUT /api/blog/<id>/ - Update blog post (admin only)
    PATCH /api/blog/<id>/ - Partial update (admin only)
    DELETE /api/blog/<id>/ - Delete blog post (admin only)
    """
    queryset = BlogPost.objects.select_related('author', 'featured_image')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method in ['PUT', 'PATCH']:
            return BlogPostCreateUpdateSerializer
        return BlogPostDetailSerializer

    def get_permissions(self):
        """Set permissions based on method."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Filter queryset based on permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Retrieve blog post and increment view count for published posts."""
        instance = self.get_object()
        
        # Only increment view count for published posts accessed by non-admin users
        if instance.is_published and not request.user.is_staff:
            instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_context(self):
        """Add request to context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BlogPostViewCountView(APIView):
    """
    Increment view count for a blog post.
    
    POST /api/blog/<id>/view/ - Increment view count
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        """Increment view count for the blog post."""
        blog_post = get_object_or_404(BlogPost, pk=pk)
        
        # Only increment for published posts
        if not blog_post.is_published:
            return Response(
                {'error': 'Blog post is not published.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        blog_post.increment_view_count()
        
        return Response({
            'id': blog_post.id,
            'title': blog_post.title,
            'view_count': blog_post.view_count,
            'message': 'View count incremented successfully.'
        }, status=status.HTTP_200_OK)
