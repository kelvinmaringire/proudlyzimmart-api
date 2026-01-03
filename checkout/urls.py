"""
URL configuration for checkout app.
Defines all checkout flow API endpoints.
"""
from django.urls import path
from .views import (
    CheckoutInitView,
    AddressView,
    ShippingMethodView,
    PaymentMethodView,
    ReviewView,
    CreateOrderView,
    PaymentCallbackView,
)

app_name = 'checkout'

urlpatterns = [
    # Initialize checkout
    path('init/', CheckoutInitView.as_view(), name='checkout-init'),
    
    # Address collection
    path('address/', AddressView.as_view(), name='checkout-address'),
    
    # Shipping method selection
    path('shipping/', ShippingMethodView.as_view(), name='checkout-shipping'),
    
    # Payment method selection
    path('payment/', PaymentMethodView.as_view(), name='checkout-payment'),
    
    # Order review
    path('review/', ReviewView.as_view(), name='checkout-review'),
    
    # Create order
    path('create-order/', CreateOrderView.as_view(), name='checkout-create-order'),
    
    # Payment callback
    path('payment/callback/', PaymentCallbackView.as_view(), name='checkout-payment-callback'),
]

