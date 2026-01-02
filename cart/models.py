"""
Cart models for ProudlyZimmart marketplace.
Handles promo codes, orders, and order items.
Note: Cart itself is stored in frontend localStorage, backend only validates and creates orders.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

from products.models import Product, ProductVariation

User = get_user_model()


class PromoCode(models.Model):
    """Promo code model for discounts."""
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Discount Type
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    
    # Discount Amount (percentage or fixed amount)
    discount_value_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Discount value in USD"
    )
    discount_value_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Discount value in ZWL RTGS"
    )
    discount_value_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Discount value in ZAR"
    )
    
    # Usage Limits
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this code can be used (null = unlimited)"
    )
    used_count = models.IntegerField(default=0)
    
    # Validity Period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    minimum_order_amount_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount in USD to use this code"
    )
    minimum_order_amount_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount in ZWL RTGS to use this code"
    )
    minimum_order_amount_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount in ZAR to use this code"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]

    def __str__(self):
        return self.code

    def is_valid(self, currency='USD', order_amount=None):
        """Check if promo code is valid for use."""
        if not self.is_active:
            return False, "Promo code is not active"
        
        if self.valid_until and timezone.now() > self.valid_until:
            return False, "Promo code has expired"
        
        if timezone.now() < self.valid_from:
            return False, "Promo code is not yet valid"
        
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "Promo code has reached maximum usage limit"
        
        # Check minimum order amount
        if order_amount is not None:
            if currency.upper() == 'USD' and self.minimum_order_amount_usd:
                if order_amount < self.minimum_order_amount_usd:
                    return False, f"Minimum order amount of ${self.minimum_order_amount_usd} required"
            elif currency.upper() == 'ZWL' and self.minimum_order_amount_zwl:
                if order_amount < self.minimum_order_amount_zwl:
                    return False, f"Minimum order amount of ZWL {self.minimum_order_amount_zwl} required"
            elif currency.upper() == 'ZAR' and self.minimum_order_amount_zar:
                if order_amount < self.minimum_order_amount_zar:
                    return False, f"Minimum order amount of ZAR {self.minimum_order_amount_zar} required"
        
        return True, "Valid"

    def calculate_discount(self, amount, currency='USD'):
        """Calculate discount amount for given order amount."""
        if currency.upper() == 'USD':
            discount_value = self.discount_value_usd
        elif currency.upper() == 'ZWL':
            discount_value = self.discount_value_zwl
        elif currency.upper() == 'ZAR':
            discount_value = self.discount_value_zar
        else:
            discount_value = self.discount_value_usd
        
        if not discount_value:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return (amount * discount_value) / Decimal('100.00')
        else:
            return min(discount_value, amount)  # Fixed amount, but can't exceed order amount


class Order(models.Model):
    """Order model for completed purchases."""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order Identification
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Order Status
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Currency
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('ZWL', 'ZWL RTGS'),
        ('ZAR', 'ZAR'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Pricing (multi-currency)
    subtotal_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    subtotal_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    subtotal_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Discount
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    discount_amount_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount_amount_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount_amount_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Shipping
    shipping_method = models.CharField(max_length=100, blank=True)
    shipping_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    shipping_cost_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    shipping_cost_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Total
    total_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Shipping Information
    shipping_first_name = models.CharField(max_length=100)
    shipping_last_name = models.CharField(max_length=100)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default='Zimbabwe')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'payment_status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import random
            import string
            while True:
                order_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                if not Order.objects.filter(order_number=order_num).exists():
                    self.order_number = order_num
                    break
        
        # Calculate totals for all currencies
        self.total_usd = (
            self.subtotal_usd - self.discount_amount_usd + self.shipping_cost_usd
        )
        self.total_zwl = (
            self.subtotal_zwl - self.discount_amount_zwl + self.shipping_cost_zwl
        )
        self.total_zar = (
            self.subtotal_zar - self.discount_amount_zar + self.shipping_cost_zar
        )
        
        super().save(*args, **kwargs)

    def get_total(self):
        """Get total for the order's currency."""
        if self.currency == 'USD':
            return self.total_usd
        elif self.currency == 'ZWL':
            return self.total_zwl
        elif self.currency == 'ZAR':
            return self.total_zar
        return self.total_usd


class OrderItem(models.Model):
    """Order item model for individual products in an order."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    
    # Product Details (snapshot at time of order)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    variation_name = models.CharField(max_length=100, blank=True)
    variation_value = models.CharField(max_length=100, blank=True)
    
    # Pricing (multi-currency)
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Subtotal (multi-currency)
    subtotal_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    subtotal_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    subtotal_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product_name} x{self.quantity} - Order {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Calculate subtotals
        self.subtotal_usd = self.price_usd * self.quantity
        self.subtotal_zwl = self.price_zwl * self.quantity
        self.subtotal_zar = self.price_zar * self.quantity
        super().save(*args, **kwargs)
