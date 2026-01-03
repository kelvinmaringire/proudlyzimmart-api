"""
Checkout models for ProudlyZimmart marketplace.
Handles checkout sessions, shipping methods, and payment transactions.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.crypto import get_random_string
from decimal import Decimal
import json

from cart.models import Order

User = get_user_model()


class CheckoutSession(models.Model):
    """
    Temporary session to track checkout state for guest or authenticated users.
    Uses token-based approach for SPA compatibility.
    """
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('address_collected', 'Address Collected'),
        ('shipping_selected', 'Shipping Selected'),
        ('payment_selected', 'Payment Selected'),
        ('order_created', 'Order Created'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Session identification (token-based for SPA)
    session_token = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions'
    )
    
    # Cart data (JSON)
    cart_data = models.JSONField(default=dict, help_text="Cart items and currency")
    
    # Addresses (JSON)
    shipping_address = models.JSONField(default=dict, null=True, blank=True)
    billing_address = models.JSONField(default=dict, null=True, blank=True)
    
    # Shipping
    selected_shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions'
    )
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
    
    # Promo code
    promo_code = models.CharField(max_length=50, blank=True)
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
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    
    # Order reference (after order creation)
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions'
    )
    
    # Expiry
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"CheckoutSession {self.session_token[:8]}... ({self.status})"

    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = get_random_string(64)
        
        if not self.expires_at:
            # Default expiry: 30 minutes from now
            from django.conf import settings
            expiry_minutes = getattr(settings, 'CHECKOUT_SESSION_EXPIRY_MINUTES', 30)
            self.expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at

    def extend_expiry(self, minutes=30):
        """Extend session expiry."""
        from django.conf import settings
        expiry_minutes = getattr(settings, 'CHECKOUT_SESSION_EXPIRY_MINUTES', minutes)
        self.expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        self.save(update_fields=['expires_at'])


class ShippingMethod(models.Model):
    """
    Configured shipping methods (The Courier Guy, DHL, Pep Paxi, etc.).
    Supports both API-based and manual rate calculation.
    """
    PROVIDER_CHOICES = [
        ('courier_guy', 'The Courier Guy'),
        ('dhl', 'DHL'),
        ('pep_paxi', 'Pep Paxi'),
        ('manual', 'Manual'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='manual'
    )
    
    is_active = models.BooleanField(default=True)
    api_enabled = models.BooleanField(
        default=False,
        help_text="Whether to use API for rate calculation"
    )
    api_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="API configuration (API keys, endpoints, etc.)"
    )
    
    # Manual rates (JSON structure: {country: {weight_range: price}})
    manual_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text="Manual shipping rates configuration"
    )
    
    # Estimated delivery time
    estimated_days_min = models.IntegerField(
        default=3,
        help_text="Minimum estimated delivery days"
    )
    estimated_days_max = models.IntegerField(
        default=7,
        help_text="Maximum estimated delivery days"
    )
    
    # Display order
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider})"


class PaymentTransaction(models.Model):
    """
    Track payment attempts and status.
    Links to Order after creation.
    """
    PAYMENT_METHOD_CHOICES = [
        ('payfast', 'PayFast'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='payfast'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # PayFast specific fields
    payfast_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    payfast_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="PayFast callback/response data"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['status', 'payment_method']),
            models.Index(fields=['payfast_payment_id']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID
            import random
            import string
            while True:
                tx_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
                if not PaymentTransaction.objects.filter(transaction_id=tx_id).exists():
                    self.transaction_id = tx_id
                    break
        
        super().save(*args, **kwargs)
