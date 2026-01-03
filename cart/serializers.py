"""
Serializers for cart app.
Handles cart validation, checkout, stock check, and promo code validation.
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone

from products.models import Product, ProductVariation
from .models import PromoCode, Order, OrderItem


class CartItemSerializer(serializers.Serializer):
    """Serializer for cart item validation."""
    product_id = serializers.IntegerField()
    variation_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    price_usd = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_zwl = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_zar = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class CartItemDetailSerializer(serializers.Serializer):
    """Serializer for enriched cart item details (for drawer display)."""
    product_id = serializers.IntegerField()
    variation_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField()
    
    # Product details
    product_name = serializers.CharField()
    product_slug = serializers.CharField()
    product_sku = serializers.CharField()
    product_image_url = serializers.CharField(required=False, allow_null=True)
    
    # Variation details
    variation_name = serializers.CharField(required=False, allow_null=True)
    variation_value = serializers.CharField(required=False, allow_null=True)
    
    # Pricing
    price_usd = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    price_zwl = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    price_zar = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Subtotal
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Stock
    available_stock = serializers.IntegerField()
    in_stock = serializers.BooleanField()


class CartValidationSerializer(serializers.Serializer):
    """Serializer for cart validation request."""
    items = CartItemSerializer(many=True)
    currency = serializers.ChoiceField(choices=['USD', 'ZWL', 'ZAR'], default='USD')
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_items(self, value):
        """Validate that items list is not empty."""
        if not value:
            raise serializers.ValidationError("Cart must contain at least one item.")
        return value


class StockCheckItemSerializer(serializers.Serializer):
    """Serializer for stock check item."""
    product_id = serializers.IntegerField()
    variation_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)


class StockCheckSerializer(serializers.Serializer):
    """Serializer for stock check request."""
    items = StockCheckItemSerializer(many=True, required=False)
    product_id = serializers.IntegerField(required=False)
    variation_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, required=False)

    def validate(self, data):
        """Validate that either items list or single product_id is provided."""
        items = data.get('items', [])
        product_id = data.get('product_id')
        
        if not items and not product_id:
            raise serializers.ValidationError(
                "Either 'items' list or 'product_id' must be provided."
            )
        
        if items and product_id:
            raise serializers.ValidationError(
                "Cannot provide both 'items' list and 'product_id'. Use one or the other."
            )
        
        return data


class PromoCodeValidationSerializer(serializers.Serializer):
    """Serializer for promo code validation request."""
    code = serializers.CharField()
    currency = serializers.ChoiceField(choices=['USD', 'ZWL', 'ZAR'], default='USD')
    order_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )


class ShippingInfoSerializer(serializers.Serializer):
    """Serializer for shipping information."""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, default='Zimbabwe')


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout request."""
    items = CartItemSerializer(many=True)
    currency = serializers.ChoiceField(choices=['USD', 'ZWL', 'ZAR'], default='USD')
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    shipping_info = ShippingInfoSerializer()
    shipping_method = serializers.CharField(max_length=100, required=False, allow_blank=True)
    shipping_cost_usd = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        required=False
    )
    shipping_cost_zwl = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        required=False
    )
    shipping_cost_zar = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        """Validate that items list is not empty."""
        if not value:
            raise serializers.ValidationError("Cart must contain at least one item.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order item."""
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variation', 'product_name', 'product_sku',
            'variation_name', 'variation_value', 'quantity',
            'price_usd', 'price_zwl', 'price_zar',
            'subtotal_usd', 'subtotal_zwl', 'subtotal_zar',
            'created_at'
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for order."""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'currency', 'subtotal_usd', 'subtotal_zwl', 'subtotal_zar',
            'promo_code', 'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar',
            'shipping_method', 'shipping_cost_usd', 'shipping_cost_zwl', 'shipping_cost_zar',
            'total_usd', 'total_zwl', 'total_zar',
            'shipping_first_name', 'shipping_last_name', 'shipping_email', 'shipping_phone',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'notes', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'subtotal_usd', 'subtotal_zwl', 'subtotal_zar',
            'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar',
            'total_usd', 'total_zwl', 'total_zar',
            'created_at', 'updated_at'
        ]


class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for promo code."""
    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount_type',
            'discount_value_usd', 'discount_value_zwl', 'discount_value_zar',
            'max_uses', 'used_count', 'valid_from', 'valid_until',
            'is_active', 'minimum_order_amount_usd', 'minimum_order_amount_zwl',
            'minimum_order_amount_zar', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at']
