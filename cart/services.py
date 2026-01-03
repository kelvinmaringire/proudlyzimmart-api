"""
Services for cart app.
Handles order creation logic that can be called from checkout app.
"""
from django.db import transaction
from decimal import Decimal

from .models import Order, OrderItem, PromoCode
from products.models import Product, ProductVariation


@transaction.atomic
def create_order_from_checkout_session(checkout_session, notes=''):
    """
    Create order from checkout session.
    Can be called from checkout app for guest or authenticated users.
    """
    from checkout.models import CheckoutSession
    
    # Get cart data
    cart_items = checkout_session.cart_data.get('items', [])
    currency = checkout_session.cart_data.get('currency', 'USD')
    
    # Get addresses
    shipping_address = checkout_session.shipping_address
    billing_address = checkout_session.billing_address or shipping_address
    
    # Validate and process items
    subtotal_usd = Decimal('0.00')
    subtotal_zwl = Decimal('0.00')
    subtotal_zar = Decimal('0.00')
    
    validated_items = []
    
    for item_data in cart_items:
        product_id = item_data['product_id']
        variation_id = item_data.get('variation_id')
        quantity = item_data['quantity']
        
        # Get product with lock
        product = Product.objects.select_for_update().get(pk=product_id)
        
        if not product.is_active:
            raise ValueError(f'Product {product_id} is not active')
        
        # Get variation if provided
        variation = None
        if variation_id:
            variation = ProductVariation.objects.select_for_update().get(
                pk=variation_id,
                product=product
            )
            if not variation.is_active:
                raise ValueError(f'Product variation {variation_id} is not active')
        
        # Check stock
        if variation:
            available_stock = variation.stock_quantity
        else:
            available_stock = product.stock_quantity
        
        if product.track_stock and available_stock < quantity:
            raise ValueError(
                f'Insufficient stock for product {product_id}. '
                f'Available: {available_stock}, Requested: {quantity}'
            )
        
        # Get prices
        price_usd = product.get_current_price('USD') or Decimal('0.00')
        price_zwl = product.get_current_price('ZWL') or Decimal('0.00')
        price_zar = product.get_current_price('ZAR') or Decimal('0.00')
        
        # Apply variation adjustments
        if variation:
            price_usd += variation.price_adjustment_usd or Decimal('0.00')
            price_zwl += variation.price_adjustment_zwl or Decimal('0.00')
            price_zar += variation.price_adjustment_zar or Decimal('0.00')
        
        # Calculate subtotals
        item_subtotal_usd = price_usd * quantity
        item_subtotal_zwl = price_zwl * quantity
        item_subtotal_zar = price_zar * quantity
        
        subtotal_usd += item_subtotal_usd
        subtotal_zwl += item_subtotal_zwl
        subtotal_zar += item_subtotal_zar
        
        # Reserve stock
        if product.track_stock:
            if variation:
                variation.stock_quantity -= quantity
                variation.save(update_fields=['stock_quantity'])
            else:
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])
        
        validated_items.append({
            'product': product,
            'variation': variation,
            'product_name': product.name,
            'product_sku': product.sku,
            'variation_name': variation.name if variation else '',
            'variation_value': variation.value if variation else '',
            'quantity': quantity,
            'price_usd': price_usd,
            'price_zwl': price_zwl,
            'price_zar': price_zar,
        })
    
    # Get promo code if provided
    promo_code = None
    if checkout_session.promo_code:
        try:
            promo_code = PromoCode.objects.get(code=checkout_session.promo_code.upper())
            # Increment usage count
            promo_code.used_count += 1
            promo_code.save(update_fields=['used_count'])
        except PromoCode.DoesNotExist:
            pass
    
    # Create order
    order = Order.objects.create(
        user=checkout_session.user,  # Can be None for guest checkout
        currency=currency,
        subtotal_usd=subtotal_usd,
        subtotal_zwl=subtotal_zwl,
        subtotal_zar=subtotal_zar,
        promo_code=promo_code,
        discount_amount_usd=checkout_session.discount_amount_usd,
        discount_amount_zwl=checkout_session.discount_amount_zwl,
        discount_amount_zar=checkout_session.discount_amount_zar,
        shipping_method=checkout_session.selected_shipping_method.name if checkout_session.selected_shipping_method else '',
        shipping_cost_usd=checkout_session.shipping_cost_usd,
        shipping_cost_zwl=checkout_session.shipping_cost_zwl,
        shipping_cost_zar=checkout_session.shipping_cost_zar,
        shipping_first_name=shipping_address['first_name'],
        shipping_last_name=shipping_address['last_name'],
        shipping_email=shipping_address['email'],
        shipping_phone=shipping_address['phone'],
        shipping_address_line1=shipping_address['address_line1'],
        shipping_address_line2=shipping_address.get('address_line2', ''),
        shipping_city=shipping_address['city'],
        shipping_state=shipping_address.get('state', ''),
        shipping_postal_code=shipping_address.get('postal_code', ''),
        shipping_country=shipping_address.get('country', 'Zimbabwe'),
        notes=notes,
        status='pending',
        payment_status='pending'
    )
    
    # Create order items
    for item_data in validated_items:
        OrderItem.objects.create(
            order=order,
            product=item_data['product'],
            variation=item_data['variation'],
            product_name=item_data['product_name'],
            product_sku=item_data['product_sku'],
            variation_name=item_data['variation_name'],
            variation_value=item_data['variation_value'],
            quantity=item_data['quantity'],
            price_usd=item_data['price_usd'],
            price_zwl=item_data['price_zwl'],
            price_zar=item_data['price_zar']
        )
    
    return order

