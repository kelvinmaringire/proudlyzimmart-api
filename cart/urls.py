"""
URL configuration for cart app.
Defines all cart-related API endpoints using Generic Views.
"""
from django.urls import path
from .views import (
    CartValidateView,
    CartItemsDetailView,
    StockCheckView,
    PromoCodeValidateView,
    CheckoutView,
    CartSyncView,
)

app_name = 'cart'

urlpatterns = [
    # Cart Validation
    path('validate/', CartValidateView.as_view(), name='cart-validate'),
    
    # Cart Items Detail (for drawer display)
    path('items-detail/', CartItemsDetailView.as_view(), name='cart-items-detail'),
    
    # Stock Check
    path('stock-check/', StockCheckView.as_view(), name='stock-check'),
    
    # Promo Code Validation
    path('promo-code/validate/', PromoCodeValidateView.as_view(), name='promo-code-validate'),
    
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Cart Sync (for login)
    path('sync/', CartSyncView.as_view(), name='cart-sync'),
]

