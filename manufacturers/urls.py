"""
URL configuration for manufacturers app.
Defines all manufacturer-related API endpoints using Generic Views.
"""
from django.urls import path
from .views import (
    ManufacturerListCreateView,
    ManufacturerDetailView,
    ManufacturerProductsView,
    ManufacturerFeaturedView,
    ManufacturerSearchView,
)

app_name = 'manufacturers'

urlpatterns = [
    # Manufacturers
    path('', ManufacturerListCreateView.as_view(), name='manufacturer-list-create'),
    path('<int:pk>/', ManufacturerDetailView.as_view(), name='manufacturer-detail'),
    path('<int:pk>/products/', ManufacturerProductsView.as_view(), name='manufacturer-products'),
    path('featured/', ManufacturerFeaturedView.as_view(), name='manufacturer-featured'),
    
    # Advanced Search
    path('search/', ManufacturerSearchView.as_view(), name='manufacturer-search'),
]

