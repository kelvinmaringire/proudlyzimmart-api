"""
Admin configuration for cart app.
"""
from django.contrib import admin
from .models import PromoCode, Order, OrderItem


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """Admin interface for PromoCode model."""
    list_display = [
        'code', 'discount_type', 'discount_value_usd', 'discount_value_zwl',
        'discount_value_zar', 'is_active', 'used_count', 'max_uses',
        'valid_from', 'valid_until', 'created_at'
    ]
    list_filter = ['is_active', 'discount_type', 'valid_from', 'valid_until']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': (
                'discount_type',
                'discount_value_usd', 'discount_value_zwl', 'discount_value_zar'
            )
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Minimum Order Amount', {
            'fields': (
                'minimum_order_amount_usd',
                'minimum_order_amount_zwl',
                'minimum_order_amount_zar'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem."""
    model = OrderItem
    readonly_fields = [
        'product', 'variation', 'product_name', 'product_sku',
        'variation_name', 'variation_value', 'quantity',
        'price_usd', 'price_zwl', 'price_zar',
        'subtotal_usd', 'subtotal_zwl', 'subtotal_zar',
        'created_at'
    ]
    can_delete = False
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'currency', 'get_total', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'currency', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_email']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at',
        'subtotal_usd', 'subtotal_zwl', 'subtotal_zar',
        'discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar',
        'total_usd', 'total_zwl', 'total_zar'
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'currency')
        }),
        ('Pricing', {
            'fields': (
                ('subtotal_usd', 'subtotal_zwl', 'subtotal_zar'),
                ('discount_amount_usd', 'discount_amount_zwl', 'discount_amount_zar'),
                ('shipping_cost_usd', 'shipping_cost_zwl', 'shipping_cost_zar'),
                ('total_usd', 'total_zwl', 'total_zar'),
            )
        }),
        ('Promo Code', {
            'fields': ('promo_code',)
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_method',
                ('shipping_first_name', 'shipping_last_name'),
                'shipping_email', 'shipping_phone',
                'shipping_address_line1', 'shipping_address_line2',
                ('shipping_city', 'shipping_state', 'shipping_postal_code'),
                'shipping_country'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_total(self, obj):
        """Display total for the order's currency."""
        return obj.get_total()
    get_total.short_description = 'Total'
