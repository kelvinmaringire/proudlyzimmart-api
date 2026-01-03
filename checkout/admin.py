"""
Admin configuration for checkout app.
"""
from django.contrib import admin
from .models import CheckoutSession, ShippingMethod, PaymentTransaction


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    """Admin for ShippingMethod model."""
    list_display = [
        'name', 'code', 'provider', 'is_active', 'api_enabled',
        'estimated_days_min', 'estimated_days_max', 'display_order'
    ]
    list_filter = ['provider', 'is_active', 'api_enabled']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'provider', 'is_active', 'display_order')
        }),
        ('API Configuration', {
            'fields': ('api_enabled', 'api_config'),
            'classes': ('collapse',)
        }),
        ('Manual Rates', {
            'fields': ('manual_rates',),
            'description': 'JSON structure: {"country": {"weight_range": price}}'
        }),
        ('Delivery Estimates', {
            'fields': ('estimated_days_min', 'estimated_days_max')
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Admin for PaymentTransaction model."""
    list_display = [
        'transaction_id', 'order', 'payment_method', 'amount', 'currency',
        'status', 'payfast_payment_id', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'currency', 'created_at']
    search_fields = ['transaction_id', 'order__order_number', 'payfast_payment_id']
    readonly_fields = [
        'transaction_id', 'order', 'payment_method', 'amount', 'currency',
        'payfast_payment_id', 'payfast_data', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'order', 'payment_method', 'amount', 'currency', 'status')
        }),
        ('PayFast Details', {
            'fields': ('payfast_payment_id', 'payfast_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
    """Admin for CheckoutSession model (for debugging)."""
    list_display = [
        'session_token_short', 'user', 'status', 'order', 'expires_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['session_token', 'user__email', 'user__username', 'order__order_number']
    readonly_fields = [
        'session_token', 'user', 'cart_data', 'shipping_address', 'billing_address',
        'selected_shipping_method', 'shipping_cost_usd', 'shipping_cost_zwl', 'shipping_cost_zar',
        'promo_code', 'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar',
        'status', 'order', 'expires_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_token', 'user', 'status', 'order', 'expires_at')
        }),
        ('Cart Data', {
            'fields': ('cart_data',),
            'classes': ('collapse',)
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address'),
            'classes': ('collapse',)
        }),
        ('Shipping', {
            'fields': (
                'selected_shipping_method',
                'shipping_cost_usd', 'shipping_cost_zwl', 'shipping_cost_zar'
            )
        }),
        ('Discounts', {
            'fields': (
                'promo_code',
                'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def session_token_short(self, obj):
        """Display shortened session token."""
        return f"{obj.session_token[:16]}..." if obj.session_token else "-"
    session_token_short.short_description = 'Session Token'
