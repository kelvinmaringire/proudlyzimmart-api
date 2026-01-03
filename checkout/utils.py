"""
Helper functions for checkout app.
"""
from decimal import Decimal
from typing import Dict, List

from products.models import Product, ProductVariation
from cart.models import PromoCode


def calculate_cart_subtotals(cart_items: List[Dict], currency: str = 'USD') -> Dict:
    """
    Calculate subtotals for cart items in all currencies.
    Returns dict with subtotal_usd, subtotal_zwl, subtotal_zar.
    """
    subtotal_usd = Decimal('0.00')
    subtotal_zwl = Decimal('0.00')
    subtotal_zar = Decimal('0.00')
    
    for item in cart_items:
        product_id = item.get('product_id')
        variation_id = item.get('variation_id')
        quantity = item.get('quantity', 1)
        
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue
        
        # Get prices
        price_usd = product.get_current_price('USD') or Decimal('0.00')
        price_zwl = product.get_current_price('ZWL') or Decimal('0.00')
        price_zar = product.get_current_price('ZAR') or Decimal('0.00')
        
        # Apply variation adjustments
        if variation_id:
            try:
                variation = ProductVariation.objects.get(
                    pk=variation_id,
                    product=product
                )
                price_usd += variation.price_adjustment_usd or Decimal('0.00')
                price_zwl += variation.price_adjustment_zwl or Decimal('0.00')
                price_zar += variation.price_adjustment_zar or Decimal('0.00')
            except ProductVariation.DoesNotExist:
                pass
        
        # Calculate subtotals
        subtotal_usd += price_usd * quantity
        subtotal_zwl += price_zwl * quantity
        subtotal_zar += price_zar * quantity
    
    return {
        'subtotal_usd': subtotal_usd,
        'subtotal_zwl': subtotal_zwl,
        'subtotal_zar': subtotal_zar,
    }


def validate_cart_items(cart_items: List[Dict], currency: str = 'USD') -> tuple:
    """
    Validate cart items and return (is_valid, errors, validated_items).
    """
    errors = []
    validated_items = []
    
    for item in cart_items:
        product_id = item.get('product_id')
        variation_id = item.get('variation_id')
        quantity = item.get('quantity', 1)
        
        # Check product exists
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            errors.append({
                'product_id': product_id,
                'error': 'Product does not exist'
            })
            continue
        
        # Check product is active
        if not product.is_active:
            errors.append({
                'product_id': product_id,
                'error': 'Product is not active'
            })
            continue
        
        # Check variation if provided
        variation = None
        if variation_id:
            try:
                variation = ProductVariation.objects.get(
                    pk=variation_id,
                    product=product
                )
                if not variation.is_active:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product variation is not active'
                    })
                    continue
            except ProductVariation.DoesNotExist:
                errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': 'Product variation does not exist'
                })
                continue
        
        # Check stock
        if variation:
            available_stock = variation.stock_quantity
        else:
            available_stock = product.stock_quantity
        
        if product.track_stock and available_stock < quantity:
            errors.append({
                'product_id': product_id,
                'variation_id': variation_id,
                'error': f'Insufficient stock. Available: {available_stock}, Requested: {quantity}'
            })
            continue
        
        # Check price exists for currency
        price = product.get_current_price(currency)
        if price is None:
            errors.append({
                'product_id': product_id,
                'variation_id': variation_id,
                'error': f'Product does not have a price in {currency}'
            })
            continue
        
        validated_items.append({
            'product_id': product_id,
            'variation_id': variation_id,
            'quantity': quantity,
            'product': product,
            'variation': variation,
        })
    
    return len(errors) == 0, errors, validated_items


def apply_promo_code(
    promo_code_str: str,
    subtotal_usd: Decimal,
    subtotal_zwl: Decimal,
    subtotal_zar: Decimal,
    currency: str = 'USD'
) -> tuple:
    """
    Apply promo code and return (promo_code_obj, discount_amount_usd, discount_amount_zwl, discount_amount_zar, error).
    """
    if not promo_code_str:
        return None, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), None
    
    try:
        promo_code = PromoCode.objects.get(code=promo_code_str.upper())
    except PromoCode.DoesNotExist:
        return None, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), 'Invalid promo code'
    
    # Validate promo code
    order_amount = subtotal_usd if currency == 'USD' else (
        subtotal_zwl if currency == 'ZWL' else subtotal_zar
    )
    
    is_valid, message = promo_code.is_valid(currency=currency, order_amount=order_amount)
    if not is_valid:
        return None, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), message
    
    # Calculate discounts
    discount_amount_usd = promo_code.calculate_discount(subtotal_usd, currency='USD')
    discount_amount_zwl = promo_code.calculate_discount(subtotal_zwl, currency='ZWL')
    discount_amount_zar = promo_code.calculate_discount(subtotal_zar, currency='ZAR')
    
    return promo_code, discount_amount_usd, discount_amount_zwl, discount_amount_zar, None


def calculate_totals(
    subtotal_usd: Decimal,
    subtotal_zwl: Decimal,
    subtotal_zar: Decimal,
    discount_amount_usd: Decimal,
    discount_amount_zwl: Decimal,
    discount_amount_zar: Decimal,
    shipping_cost_usd: Decimal,
    shipping_cost_zwl: Decimal,
    shipping_cost_zar: Decimal
) -> Dict:
    """Calculate final totals."""
    total_usd = subtotal_usd - discount_amount_usd + shipping_cost_usd
    total_zwl = subtotal_zwl - discount_amount_zwl + shipping_cost_zwl
    total_zar = subtotal_zar - discount_amount_zar + shipping_cost_zar
    
    return {
        'total_usd': total_usd,
        'total_zwl': total_zwl,
        'total_zar': total_zar,
    }

