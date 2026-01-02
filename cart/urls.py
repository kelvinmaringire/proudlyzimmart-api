"""
URL configuration for cart app.
Defines all cart-related API endpoints using Generic Views.
"""
from django.urls import path
from .views import (
    CartValidateView,
    StockCheckView,
    PromoCodeValidateView,
    CheckoutView,
    CartSyncView,
)

app_name = 'cart'

urlpatterns = [
    # Cart Validation
    path('validate/', CartValidateView.as_view(), name='cart-validate'),
    
    # Stock Check
    path('stock-check/', StockCheckView.as_view(), name='stock-check'),
    
    # Promo Code Validation
    path('promo-code/validate/', PromoCodeValidateView.as_view(), name='promo-code-validate'),
    
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Cart Sync (for login)
    path('sync/', CartSyncView.as_view(), name='cart-sync'),
]

