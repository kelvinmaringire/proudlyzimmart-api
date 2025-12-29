"""
URL configuration for products app.
Defines all product-related API endpoints using Generic Views.
"""
from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    ProductTypeListView,
    ProductListCreateView,
    ProductDetailView,
    ProductVariationsView,
    ProductImagesView,
    ProductVideosView,
    ProductReviewsView,
    ProductAddReviewView,
    ProductRelatedProductsView,
    ProductFeaturedView,
    ProductOnSaleView,
    ProductSearchView,
    ProductVariationListCreateView,
    ProductVariationDetailView,
    ProductImageListCreateView,
    ProductImageDetailView,
    ProductVideoListCreateView,
    ProductVideoDetailView,
    ReviewListCreateView,
    ReviewDetailView,
    ReviewMarkHelpfulView,
    RelatedProductListCreateView,
    RelatedProductDetailView,
    ProductBundleListCreateView,
    ProductBundleDetailView,
    ProductBundleItemsView,
    ProductBundleFeaturedView,
)

app_name = 'products'

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Product Types
    path('types/', ProductTypeListView.as_view(), name='product-type-list'),
    
    # Products
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/variations/', ProductVariationsView.as_view(), name='product-variations'),
    path('products/<int:pk>/images/', ProductImagesView.as_view(), name='product-images'),
    path('products/<int:pk>/videos/', ProductVideosView.as_view(), name='product-videos'),
    path('products/<int:pk>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/<int:pk>/add_review/', ProductAddReviewView.as_view(), name='product-add-review'),
    path('products/<int:pk>/related/', ProductRelatedProductsView.as_view(), name='product-related'),
    path('products/featured/', ProductFeaturedView.as_view(), name='product-featured'),
    path('products/on-sale/', ProductOnSaleView.as_view(), name='product-on-sale'),
    
    # Advanced Search
    path('search/', ProductSearchView.as_view(), name='product-search'),
    
    # Product Variations
    path('variations/', ProductVariationListCreateView.as_view(), name='variation-list-create'),
    path('variations/<int:pk>/', ProductVariationDetailView.as_view(), name='variation-detail'),
    
    # Product Images
    path('images/', ProductImageListCreateView.as_view(), name='image-list-create'),
    path('images/<int:pk>/', ProductImageDetailView.as_view(), name='image-detail'),
    
    # Product Videos
    path('videos/', ProductVideoListCreateView.as_view(), name='video-list-create'),
    path('videos/<int:pk>/', ProductVideoDetailView.as_view(), name='video-detail'),
    
    # Reviews
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:pk>/mark_helpful/', ReviewMarkHelpfulView.as_view(), name='review-mark-helpful'),
    
    # Related Products
    path('related/', RelatedProductListCreateView.as_view(), name='related-product-list-create'),
    path('related/<int:pk>/', RelatedProductDetailView.as_view(), name='related-product-detail'),
    
    # Product Bundles
    path('bundles/', ProductBundleListCreateView.as_view(), name='bundle-list-create'),
    path('bundles/<int:pk>/', ProductBundleDetailView.as_view(), name='bundle-detail'),
    path('bundles/<int:pk>/items/', ProductBundleItemsView.as_view(), name='bundle-items'),
    path('bundles/featured/', ProductBundleFeaturedView.as_view(), name='bundle-featured'),
]
