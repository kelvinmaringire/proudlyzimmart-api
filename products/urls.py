"""
URL configuration for products app.
Defines all product-related API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryListView,
    CategoryDetailView,
    ProductTypeListView,
    ProductViewSet,
    ProductVariationViewSet,
    ProductImageViewSet,
    ReviewViewSet,
    RelatedProductViewSet,
    ProductSearchView,
    ProductVideoViewSet,
    ProductBundleViewSet,
)

app_name = 'products'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variations', ProductVariationViewSet, basename='variation')
router.register(r'images', ProductImageViewSet, basename='image')
router.register(r'videos', ProductVideoViewSet, basename='video')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'related', RelatedProductViewSet, basename='related-product')
router.register(r'bundles', ProductBundleViewSet, basename='bundle')

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Product Types
    path('types/', ProductTypeListView.as_view(), name='product-type-list'),
    
    # Advanced Search
    path('search/', ProductSearchView.as_view(), name='product-search'),
    
    # Include router URLs
    path('', include(router.urls)),
]

