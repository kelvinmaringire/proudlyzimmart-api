"""
API views for cart app.
Handles cart validation, checkout, stock check, and promo code validation.
All views use DRF Generic Views instead of ViewSets.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

from products.models import Product, ProductVariation
from .models import PromoCode, Order, OrderItem
from .serializers import (
    CartValidationSerializer,
    CartItemDetailSerializer,
    StockCheckSerializer,
    PromoCodeValidationSerializer,
    CheckoutSerializer,
    OrderSerializer,
    PromoCodeSerializer,
)


class CartValidateView(APIView):
    """
    Validate cart items before checkout.
    
    POST /api/cart/validate/
    Validates products exist, are active, stock availability, and prices.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CartValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items = serializer.validated_data['items']
        currency = serializer.validated_data.get('currency', 'USD')
        promo_code_str = serializer.validated_data.get('promo_code', '').strip()
        
        errors = []
        warnings = []
        validated_items = []
        
        # Validate promo code if provided
        promo_code = None
        if promo_code_str:
            try:
                promo_code = PromoCode.objects.get(code=promo_code_str.upper())
                is_valid, message = promo_code.is_valid(currency=currency)
                if not is_valid:
                    errors.append({'promo_code': message})
            except PromoCode.DoesNotExist:
                errors.append({'promo_code': 'Invalid promo code'})
        
        # Calculate subtotal for promo code validation
        subtotal = Decimal('0.00')
        
        # Validate each cart item
        for item_data in items:
            product_id = item_data['product_id']
            variation_id = item_data.get('variation_id')
            quantity = item_data['quantity']
            
            # Check if product exists
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product does not exist'
                })
                continue
            
            # Check if product is active
            if not product.is_active:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product is not active'
                })
                continue
            
            # Get variation if provided
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
            
            # Check stock availability
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
            
            # Get current price
            if currency == 'USD':
                current_price = product.get_current_price('USD')
                if current_price is None:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product does not have a price in USD'
                    })
                    continue
                if variation:
                    current_price += variation.price_adjustment_usd or Decimal('0.00')
            elif currency == 'ZWL':
                current_price = product.get_current_price('ZWL')
                if current_price is None:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product does not have a price in ZWL'
                    })
                    continue
                if variation:
                    current_price += variation.price_adjustment_zwl or Decimal('0.00')
            elif currency == 'ZAR':
                current_price = product.get_current_price('ZAR')
                if current_price is None:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product does not have a price in ZAR'
                    })
                    continue
                if variation:
                    current_price += variation.price_adjustment_zar or Decimal('0.00')
            else:
                current_price = product.get_current_price('USD')
                if current_price is None:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product does not have a price'
                    })
                    continue
            
            # Check if price matches (allow 5% tolerance)
            price_key = f'price_{currency.lower()}'
            provided_price = item_data.get(price_key)
            if provided_price and current_price:
                price_diff = abs(float(current_price) - float(provided_price))
                price_tolerance = float(current_price) * 0.05  # 5% tolerance
                if price_diff > price_tolerance:
                    warnings.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'warning': f'Price has changed. Current: {current_price}, Provided: {provided_price}'
                    })
            
            # Add to validated items
            validated_items.append({
                'product_id': product_id,
                'variation_id': variation_id,
                'quantity': quantity,
                'current_price': str(current_price),
                'available_stock': available_stock
            })
            
            # Add to subtotal
            subtotal += current_price * quantity
        
        # Validate promo code against order amount
        if promo_code and not errors:
            is_valid, message = promo_code.is_valid(
                currency=currency,
                order_amount=subtotal
            )
            if not is_valid:
                errors.append({'promo_code': message})
        
        if errors:
            return Response({
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'valid': True,
            'items': validated_items,
            'subtotal': str(subtotal),
            'currency': currency,
            'warnings': warnings,
            'promo_code_valid': promo_code is not None
        })


class StockCheckView(APIView):
    """
    Check stock availability for products.
    
    GET /api/cart/stock-check/?product_id=1&variation_id=2&quantity=3
    POST /api/cart/stock-check/ with items list
    Returns stock status for single product or bulk cart items.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle GET request for single product stock check."""
        product_id = request.query_params.get('product_id')
        variation_id = request.query_params.get('variation_id')
        quantity = request.query_params.get('quantity', 1)
        
        if not product_id:
            return Response({
                'error': 'product_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
        except ValueError:
            return Response({
                'error': 'quantity must be a valid integer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return self._check_stock(product_id, variation_id, quantity)

    def post(self, request):
        """Handle POST request for bulk stock check."""
        serializer = StockCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items = serializer.validated_data.get('items', [])
        product_id = serializer.validated_data.get('product_id')
        variation_id = serializer.validated_data.get('variation_id')
        quantity = serializer.validated_data.get('quantity', 1)
        
        if items:
            # Bulk check
            results = []
            for item in items:
                result = self._check_stock(
                    item['product_id'],
                    item.get('variation_id'),
                    item['quantity']
                )
                results.append(result.data)
            
            return Response({
                'results': results
            })
        else:
            # Single product check
            return self._check_stock(product_id, variation_id, quantity)

    def _check_stock(self, product_id, variation_id, quantity):
        """Check stock for a single product/variation."""
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({
                'product_id': product_id,
                'available': False,
                'error': 'Product does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not product.is_active:
            return Response({
                'product_id': product_id,
                'available': False,
                'error': 'Product is not active'
            })
        
        variation = None
        if variation_id:
            try:
                variation = ProductVariation.objects.get(
                    pk=variation_id,
                    product=product
                )
                if not variation.is_active:
                    return Response({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'available': False,
                        'error': 'Product variation is not active'
                    })
            except ProductVariation.DoesNotExist:
                return Response({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'available': False,
                    'error': 'Product variation does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get stock quantity
        if variation:
            available_stock = variation.stock_quantity
        else:
            available_stock = product.stock_quantity
        
        # Check availability
        if not product.track_stock:
            available = True
            message = 'Stock tracking disabled for this product'
        else:
            available = available_stock >= quantity
            if available:
                message = f'Available: {available_stock} in stock'
            else:
                message = f'Insufficient stock. Available: {available_stock}, Requested: {quantity}'
        
        return Response({
            'product_id': product_id,
            'variation_id': variation_id,
            'quantity': quantity,
            'available': available,
            'available_stock': available_stock,
            'message': message
        })


class PromoCodeValidateView(APIView):
    """
    Validate promo code.
    
    POST /api/cart/promo-code/validate/
    Validates promo code exists, is active, and returns discount details.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PromoCodeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code'].strip().upper()
        currency = serializer.validated_data.get('currency', 'USD')
        order_amount = serializer.validated_data.get('order_amount')
        
        try:
            promo_code = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid promo code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate promo code
        is_valid, message = promo_code.is_valid(
            currency=currency,
            order_amount=order_amount
        )
        
        if not is_valid:
            return Response({
                'valid': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate discount if order amount provided
        discount_amount = None
        if order_amount:
            discount_amount = promo_code.calculate_discount(
                Decimal(str(order_amount)),
                currency=currency
            )
        
        # Get discount value for currency
        if currency == 'USD':
            discount_value = promo_code.discount_value_usd
        elif currency == 'ZWL':
            discount_value = promo_code.discount_value_zwl
        elif currency == 'ZAR':
            discount_value = promo_code.discount_value_zar
        else:
            discount_value = promo_code.discount_value_usd
        
        return Response({
            'valid': True,
            'code': promo_code.code,
            'description': promo_code.description,
            'discount_type': promo_code.discount_type,
            'discount_value': str(discount_value) if discount_value else None,
            'discount_amount': str(discount_amount) if discount_amount else None,
            'currency': currency
        })


class CheckoutView(APIView):
    """
    Create order from cart data.
    
    POST /api/cart/checkout/
    Validates cart items and creates order records.
    Requires authentication.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items = serializer.validated_data['items']
        currency = serializer.validated_data.get('currency', 'USD')
        promo_code_str = serializer.validated_data.get('promo_code', '').strip()
        shipping_info = serializer.validated_data['shipping_info']
        shipping_method = serializer.validated_data.get('shipping_method', '')
        shipping_cost_usd = serializer.validated_data.get('shipping_cost_usd', Decimal('0.00'))
        shipping_cost_zwl = serializer.validated_data.get('shipping_cost_zwl', Decimal('0.00'))
        shipping_cost_zar = serializer.validated_data.get('shipping_cost_zar', Decimal('0.00'))
        notes = serializer.validated_data.get('notes', '')
        
        # Validate all items first
        validation_errors = []
        validated_items = []
        subtotal_usd = Decimal('0.00')
        subtotal_zwl = Decimal('0.00')
        subtotal_zar = Decimal('0.00')
        
        for item_data in items:
            product_id = item_data['product_id']
            variation_id = item_data.get('variation_id')
            quantity = item_data['quantity']
            
            try:
                product = Product.objects.select_for_update().get(pk=product_id)
            except Product.DoesNotExist:
                validation_errors.append({
                    'product_id': product_id,
                    'error': 'Product does not exist'
                })
                continue
            
            if not product.is_active:
                validation_errors.append({
                    'product_id': product_id,
                    'error': 'Product is not active'
                })
                continue
            
            variation = None
            if variation_id:
                try:
                    variation = ProductVariation.objects.select_for_update().get(
                        pk=variation_id,
                        product=product
                    )
                    if not variation.is_active:
                        validation_errors.append({
                            'product_id': product_id,
                            'variation_id': variation_id,
                            'error': 'Product variation is not active'
                        })
                        continue
                except ProductVariation.DoesNotExist:
                    validation_errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product variation does not exist'
                    })
                    continue
            
            # Check stock and reserve
            if variation:
                available_stock = variation.stock_quantity
            else:
                available_stock = product.stock_quantity
            
            if product.track_stock and available_stock < quantity:
                validation_errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': f'Insufficient stock. Available: {available_stock}, Requested: {quantity}'
                })
                continue
            
            # Get prices
            price_usd = product.get_current_price('USD')
            price_zwl = product.get_current_price('ZWL')
            price_zar = product.get_current_price('ZAR')
            
            # Validate price exists for requested currency
            if currency == 'USD' and price_usd is None:
                validation_errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': 'Product does not have a price in USD'
                })
                continue
            elif currency == 'ZWL' and price_zwl is None:
                validation_errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': 'Product does not have a price in ZWL'
                })
                continue
            elif currency == 'ZAR' and price_zar is None:
                validation_errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': 'Product does not have a price in ZAR'
                })
                continue
            
            # Use 0.00 as fallback for other currencies (for subtotal calculation)
            price_usd = price_usd or Decimal('0.00')
            price_zwl = price_zwl or Decimal('0.00')
            price_zar = price_zar or Decimal('0.00')
            
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
        
        if validation_errors:
            return Response({
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and apply promo code
        promo_code = None
        discount_amount_usd = Decimal('0.00')
        discount_amount_zwl = Decimal('0.00')
        discount_amount_zar = Decimal('0.00')
        
        if promo_code_str:
            try:
                promo_code = PromoCode.objects.get(code=promo_code_str.upper())
                is_valid, message = promo_code.is_valid(
                    currency=currency,
                    order_amount=subtotal_usd if currency == 'USD' else
                                subtotal_zwl if currency == 'ZWL' else subtotal_zar
                )
                if not is_valid:
                    return Response({
                        'error': f'Promo code validation failed: {message}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate discount
                if currency == 'USD':
                    discount_amount_usd = promo_code.calculate_discount(subtotal_usd, currency='USD')
                elif currency == 'ZWL':
                    discount_amount_zwl = promo_code.calculate_discount(subtotal_zwl, currency='ZWL')
                elif currency == 'ZAR':
                    discount_amount_zar = promo_code.calculate_discount(subtotal_zar, currency='ZAR')
                
                # Increment usage count
                promo_code.used_count += 1
                promo_code.save(update_fields=['used_count'])
            except PromoCode.DoesNotExist:
                return Response({
                    'error': 'Invalid promo code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            currency=currency,
            subtotal_usd=subtotal_usd,
            subtotal_zwl=subtotal_zwl,
            subtotal_zar=subtotal_zar,
            promo_code=promo_code,
            discount_amount_usd=discount_amount_usd,
            discount_amount_zwl=discount_amount_zwl,
            discount_amount_zar=discount_amount_zar,
            shipping_method=shipping_method,
            shipping_cost_usd=shipping_cost_usd,
            shipping_cost_zwl=shipping_cost_zwl,
            shipping_cost_zar=shipping_cost_zar,
            shipping_first_name=shipping_info['first_name'],
            shipping_last_name=shipping_info['last_name'],
            shipping_email=shipping_info['email'],
            shipping_phone=shipping_info['phone'],
            shipping_address_line1=shipping_info['address_line1'],
            shipping_address_line2=shipping_info.get('address_line2', ''),
            shipping_city=shipping_info['city'],
            shipping_state=shipping_info.get('state', ''),
            shipping_postal_code=shipping_info.get('postal_code', ''),
            shipping_country=shipping_info.get('country', 'Zimbabwe'),
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
        
        # Serialize and return order
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)


class CartItemsDetailView(APIView):
    """
    Get enriched cart items details for drawer display.
    
    POST /api/cart/items-detail/
    Takes cart items from localStorage and returns enriched product data
    with images, names, prices, etc. for display in cart drawer.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CartValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items = serializer.validated_data['items']
        currency = serializer.validated_data.get('currency', 'USD')
        
        enriched_items = []
        errors = []
        
        for item_data in items:
            product_id = item_data['product_id']
            variation_id = item_data.get('variation_id')
            quantity = item_data['quantity']
            
            try:
                product = Product.objects.select_related('category', 'product_type').prefetch_related(
                    'images'
                ).get(pk=product_id)
            except Product.DoesNotExist:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product does not exist'
                })
                continue
            
            if not product.is_active:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product is not active'
                })
                continue
            
            # Get variation if provided
            variation = None
            variation_name = None
            variation_value = None
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
                    variation_name = variation.name
                    variation_value = variation.value
                except ProductVariation.DoesNotExist:
                    errors.append({
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'error': 'Product variation does not exist'
                    })
                    continue
            
            # Get product image
            primary_image = product.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = product.images.first()
            
            image_url = None
            if primary_image and primary_image.image and primary_image.image.file:
                request_obj = request
                image_url = request_obj.build_absolute_uri(primary_image.image.file.url)
            
            # Get prices
            price_usd = product.get_current_price('USD')
            price_zwl = product.get_current_price('ZWL')
            price_zar = product.get_current_price('ZAR')
            
            if variation:
                if price_usd:
                    price_usd += variation.price_adjustment_usd or Decimal('0.00')
                if price_zwl:
                    price_zwl += variation.price_adjustment_zwl or Decimal('0.00')
                if price_zar:
                    price_zar += variation.price_adjustment_zar or Decimal('0.00')
            
            # Get current price for selected currency
            if currency == 'USD':
                current_price = price_usd
            elif currency == 'ZWL':
                current_price = price_zwl
            elif currency == 'ZAR':
                current_price = price_zar
            else:
                current_price = price_usd
            
            if current_price is None:
                errors.append({
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'error': f'Product does not have a price in {currency}'
                })
                continue
            
            # Calculate subtotal
            subtotal = current_price * quantity
            
            # Get stock info
            if variation:
                available_stock = variation.stock_quantity
            else:
                available_stock = product.stock_quantity
            
            in_stock = True
            if product.track_stock:
                in_stock = available_stock > 0
            
            enriched_items.append({
                'product_id': product_id,
                'variation_id': variation_id,
                'quantity': quantity,
                'product_name': product.name,
                'product_slug': product.slug,
                'product_sku': product.sku,
                'product_image_url': image_url,
                'variation_name': variation_name,
                'variation_value': variation_value,
                'price_usd': str(price_usd) if price_usd else None,
                'price_zwl': str(price_zwl) if price_zwl else None,
                'price_zar': str(price_zar) if price_zar else None,
                'current_price': str(current_price),
                'subtotal': str(subtotal),
                'available_stock': available_stock,
                'in_stock': in_stock,
            })
        
        if errors:
            return Response({
                'items': enriched_items,
                'errors': errors,
                'currency': currency
            }, status=status.HTTP_200_OK)
        
        return Response({
            'items': enriched_items,
            'currency': currency
        })


class CartSyncView(APIView):
    """
    Sync cart when user logs in.
    
    POST /api/cart/sync/
    Merges localStorage cart with backend (if needed in future).
    Currently just validates the cart items.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CartValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # For now, just validate the cart
        # In future, could merge with any saved cart items
        items = serializer.validated_data['items']
        currency = serializer.validated_data.get('currency', 'USD')
        
        # Use the same validation logic as CartValidateView
        errors = []
        validated_items = []
        
        for item_data in items:
            product_id = item_data['product_id']
            variation_id = item_data.get('variation_id')
            quantity = item_data['quantity']
            
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product does not exist'
                })
                continue
            
            if not product.is_active:
                errors.append({
                    'product_id': product_id,
                    'error': 'Product is not active'
                })
                continue
            
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
            
            validated_items.append({
                'product_id': product_id,
                'variation_id': variation_id,
                'quantity': quantity
            })
        
        if errors:
            return Response({
                'synced': False,
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'synced': True,
            'items': validated_items,
            'currency': currency,
            'message': 'Cart validated successfully'
        })
