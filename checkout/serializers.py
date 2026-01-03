"""
Serializers for checkout app.
Handles all checkout step serialization.
"""
from rest_framework import serializers
from decimal import Decimal

from .models import CheckoutSession, ShippingMethod, PaymentTransaction
from cart.models import PromoCode
from cart.serializers import CartItemSerializer, ShippingInfoSerializer


class CheckoutInitSerializer(serializers.Serializer):
    """Serializer for checkout initialization."""
    items = CartItemSerializer(many=True)
    currency = serializers.ChoiceField(choices=['USD', 'ZWL', 'ZAR'], default='USD')
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_items(self, value):
        """Validate that items list is not empty."""
        if not value:
            raise serializers.ValidationError("Cart must contain at least one item.")
        return value


class AddressSerializer(serializers.Serializer):
    """Serializer for shipping/billing address."""
    shipping_address = ShippingInfoSerializer()
    billing_address = ShippingInfoSerializer(required=False, allow_null=True)
    use_billing_as_shipping = serializers.BooleanField(default=False)

    def validate(self, data):
        """If use_billing_as_shipping is True, copy shipping to billing."""
        if data.get('use_billing_as_shipping', False):
            if not data.get('billing_address'):
                data['billing_address'] = data['shipping_address']
        return data


class ShippingMethodSerializer(serializers.ModelSerializer):
    """Serializer for shipping method selection."""
    class Meta:
        model = ShippingMethod
        fields = [
            'id', 'name', 'code', 'provider', 'is_active',
            'estimated_days_min', 'estimated_days_max', 'display_order'
        ]
        read_only_fields = fields


class ShippingMethodSelectionSerializer(serializers.Serializer):
    """Serializer for shipping method selection."""
    shipping_method_id = serializers.IntegerField()
    shipping_address = ShippingInfoSerializer(required=False)


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer for payment method selection."""
    payment_method = serializers.ChoiceField(choices=['payfast'], default='payfast')
    return_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class CheckoutReviewSerializer(serializers.Serializer):
    """Serializer for checkout review data."""
    session_token = serializers.CharField()
    
    # Items
    items = serializers.ListField()
    currency = serializers.CharField()
    
    # Addresses
    shipping_address = serializers.DictField()
    billing_address = serializers.DictField(required=False, allow_null=True)
    
    # Shipping
    shipping_method = ShippingMethodSerializer(required=False, allow_null=True)
    shipping_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost_zwl = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost_zar = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Discounts
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount_amount_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount_zwl = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount_zar = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Totals
    subtotal_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal_zwl = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal_zar = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_zwl = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_zar = serializers.DecimalField(max_digits=10, decimal_places=2)


class CheckoutSessionSerializer(serializers.ModelSerializer):
    """Serializer for checkout session state."""
    class Meta:
        model = CheckoutSession
        fields = [
            'session_token', 'status', 'cart_data', 'shipping_address',
            'billing_address', 'selected_shipping_method', 'shipping_cost_usd',
            'shipping_cost_zwl', 'shipping_cost_zar', 'promo_code',
            'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar',
            'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transaction."""
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'transaction_id', 'order', 'payment_method', 'amount',
            'currency', 'status', 'payfast_payment_id', 'payfast_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for order creation."""
    session_token = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)

