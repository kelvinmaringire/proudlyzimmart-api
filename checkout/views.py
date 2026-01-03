"""
API views for checkout app.
Handles multi-step checkout flow from cart to order creation.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from decimal import Decimal

from .models import CheckoutSession, ShippingMethod, PaymentTransaction
from .serializers import (
    CheckoutInitSerializer,
    AddressSerializer,
    ShippingMethodSerializer,
    ShippingMethodSelectionSerializer,
    PaymentMethodSerializer,
    CheckoutReviewSerializer,
    CreateOrderSerializer,
    CheckoutSessionSerializer,
    PaymentTransactionSerializer,
)
from .services import ShippingRateService, PayFastService
from .utils import (
    calculate_cart_subtotals,
    validate_cart_items,
    apply_promo_code,
    calculate_totals,
)
from cart.models import Order
from cart import services as cart_services


class CheckoutInitView(APIView):
    """
    Initialize checkout session.
    
    POST /api/checkout/init/
    Creates CheckoutSession and validates cart items.
    Supports both guest and authenticated users.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CheckoutInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items = serializer.validated_data['items']
        currency = serializer.validated_data.get('currency', 'USD')
        promo_code_str = serializer.validated_data.get('promo_code', '').strip()
        
        # Validate cart items
        is_valid, errors, validated_items = validate_cart_items(items, currency)
        if not is_valid:
            return Response({
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate subtotals
        subtotals = calculate_cart_subtotals(items, currency)
        
        # Apply promo code if provided
        promo_code_obj, discount_usd, discount_zwl, discount_zar, promo_error = apply_promo_code(
            promo_code_str,
            subtotals['subtotal_usd'],
            subtotals['subtotal_zwl'],
            subtotals['subtotal_zar'],
            currency
        )
        
        if promo_error:
            return Response({
                'error': promo_error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create checkout session
        checkout_session = CheckoutSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cart_data={
                'items': items,
                'currency': currency
            },
            promo_code=promo_code_str.upper() if promo_code_str else '',
            discount_amount_usd=discount_usd,
            discount_amount_zwl=discount_zwl,
            discount_amount_zar=discount_zar,
            status='initiated'
        )
        
        return Response({
            'session_token': checkout_session.session_token,
            'status': checkout_session.status,
            'expires_at': checkout_session.expires_at,
            'subtotals': subtotals,
            'discounts': {
                'discount_amount_usd': str(discount_usd),
                'discount_amount_zwl': str(discount_zwl),
                'discount_amount_zar': str(discount_zar),
            },
            'currency': currency
        }, status=status.HTTP_201_CREATED)


class AddressView(APIView):
    """
    Collect shipping and billing addresses.
    
    POST /api/checkout/address/
    Saves addresses to CheckoutSession and returns available shipping methods.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_token = request.data.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checkout_session = CheckoutSession.objects.get(session_token=session_token)
        except CheckoutSession.DoesNotExist:
            return Response({
                'error': 'Invalid session token'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if checkout_session.is_expired():
            return Response({
                'error': 'Checkout session has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        shipping_address = serializer.validated_data['shipping_address']
        billing_address = serializer.validated_data.get('billing_address')
        
        # Update session
        checkout_session.shipping_address = shipping_address
        checkout_session.billing_address = billing_address or shipping_address
        checkout_session.status = 'address_collected'
        checkout_session.extend_expiry()
        checkout_session.save()
        
        # Calculate shipping rates
        cart_items = checkout_session.cart_data.get('items', [])
        currency = checkout_session.cart_data.get('currency', 'USD')
        
        shipping_rates = ShippingRateService.calculate_shipping_rates(
            shipping_address,
            cart_items,
            currency
        )
        
        # Serialize shipping methods
        available_methods = []
        for rate_data in shipping_rates:
            method = rate_data['shipping_method']
            method_serializer = ShippingMethodSerializer(method)
            available_methods.append({
                **method_serializer.data,
                'cost_usd': str(rate_data['cost_usd']),
                'cost_zwl': str(rate_data['cost_zwl']),
                'cost_zar': str(rate_data['cost_zar']),
                'estimated_days_min': rate_data['estimated_days_min'],
                'estimated_days_max': rate_data['estimated_days_max'],
            })
        
        return Response({
            'session_token': checkout_session.session_token,
            'status': checkout_session.status,
            'shipping_address': shipping_address,
            'billing_address': checkout_session.billing_address,
            'available_shipping_methods': available_methods
        }, status=status.HTTP_200_OK)


class ShippingMethodView(APIView):
    """
    Select shipping method.
    
    POST /api/checkout/shipping/
    Accepts selected shipping method ID and updates CheckoutSession.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ShippingMethodSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_token = request.data.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checkout_session = CheckoutSession.objects.get(session_token=session_token)
        except CheckoutSession.DoesNotExist:
            return Response({
                'error': 'Invalid session token'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if checkout_session.is_expired():
            return Response({
                'error': 'Checkout session has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        shipping_method_id = serializer.validated_data['shipping_method_id']
        
        try:
            shipping_method = ShippingMethod.objects.get(
                pk=shipping_method_id,
                is_active=True
            )
        except ShippingMethod.DoesNotExist:
            return Response({
                'error': 'Invalid shipping method'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Recalculate shipping rates to get cost
        shipping_address = checkout_session.shipping_address
        cart_items = checkout_session.cart_data.get('items', [])
        currency = checkout_session.cart_data.get('currency', 'USD')
        
        shipping_rates = ShippingRateService.calculate_shipping_rates(
            shipping_address,
            cart_items,
            currency
        )
        
        # Find selected method rate
        selected_rate = None
        for rate_data in shipping_rates:
            if rate_data['shipping_method'].id == shipping_method_id:
                selected_rate = rate_data
                break
        
        if not selected_rate:
            return Response({
                'error': 'Shipping rate not available for selected method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update session
        checkout_session.selected_shipping_method = shipping_method
        checkout_session.shipping_cost_usd = selected_rate['cost_usd']
        checkout_session.shipping_cost_zwl = selected_rate['cost_zwl']
        checkout_session.shipping_cost_zar = selected_rate['cost_zar']
        checkout_session.status = 'shipping_selected'
        checkout_session.extend_expiry()
        checkout_session.save()
        
        # Calculate totals
        subtotals = calculate_cart_subtotals(cart_items, currency)
        totals = calculate_totals(
            subtotals['subtotal_usd'],
            subtotals['subtotal_zwl'],
            subtotals['subtotal_zar'],
            checkout_session.discount_amount_usd,
            checkout_session.discount_amount_zwl,
            checkout_session.discount_amount_zar,
            checkout_session.shipping_cost_usd,
            checkout_session.shipping_cost_zwl,
            checkout_session.shipping_cost_zar
        )
        
        return Response({
            'session_token': checkout_session.session_token,
            'status': checkout_session.status,
            'shipping_method': ShippingMethodSerializer(shipping_method).data,
            'shipping_costs': {
                'cost_usd': str(checkout_session.shipping_cost_usd),
                'cost_zwl': str(checkout_session.shipping_cost_zwl),
                'cost_zar': str(checkout_session.shipping_cost_zar),
            },
            'totals': {
                'subtotal_usd': str(subtotals['subtotal_usd']),
                'subtotal_zwl': str(subtotals['subtotal_zwl']),
                'subtotal_zar': str(subtotals['subtotal_zar']),
                'discount_amount_usd': str(checkout_session.discount_amount_usd),
                'discount_amount_zwl': str(checkout_session.discount_amount_zwl),
                'discount_amount_zar': str(checkout_session.discount_amount_zar),
                'shipping_cost_usd': str(checkout_session.shipping_cost_usd),
                'shipping_cost_zwl': str(checkout_session.shipping_cost_zwl),
                'shipping_cost_zar': str(checkout_session.shipping_cost_zar),
                'total_usd': str(totals['total_usd']),
                'total_zwl': str(totals['total_zwl']),
                'total_zar': str(totals['total_zar']),
            },
            'currency': currency
        }, status=status.HTTP_200_OK)


class PaymentMethodView(APIView):
    """
    Select payment method.
    
    POST /api/checkout/payment/
    Currently only PayFast supported. Prepares payment data.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_token = request.data.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checkout_session = CheckoutSession.objects.get(session_token=session_token)
        except CheckoutSession.DoesNotExist:
            return Response({
                'error': 'Invalid session token'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if checkout_session.is_expired():
            return Response({
                'error': 'Checkout session has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all steps completed
        if checkout_session.status != 'shipping_selected':
            return Response({
                'error': 'Please complete shipping selection first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = serializer.validated_data.get('payment_method', 'payfast')
        
        # Update session status
        checkout_session.status = 'payment_selected'
        checkout_session.extend_expiry()
        checkout_session.save()
        
        return Response({
            'session_token': checkout_session.session_token,
            'status': checkout_session.status,
            'payment_method': payment_method,
            'message': 'Payment method selected. Proceed to create order.'
        }, status=status.HTTP_200_OK)


class ReviewView(APIView):
    """
    Get checkout review summary.
    
    GET /api/checkout/review/?session_token=xxx
    Returns complete checkout summary before order creation.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        session_token = request.query_params.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checkout_session = CheckoutSession.objects.get(session_token=session_token)
        except CheckoutSession.DoesNotExist:
            return Response({
                'error': 'Invalid session token'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if checkout_session.is_expired():
            return Response({
                'error': 'Checkout session has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate subtotals
        cart_items = checkout_session.cart_data.get('items', [])
        currency = checkout_session.cart_data.get('currency', 'USD')
        subtotals = calculate_cart_subtotals(cart_items, currency)
        
        # Calculate totals
        totals = calculate_totals(
            subtotals['subtotal_usd'],
            subtotals['subtotal_zwl'],
            subtotals['subtotal_zar'],
            checkout_session.discount_amount_usd,
            checkout_session.discount_amount_zwl,
            checkout_session.discount_amount_zar,
            checkout_session.shipping_cost_usd,
            checkout_session.shipping_cost_zwl,
            checkout_session.shipping_cost_zar
        )
        
        # Get shipping method
        shipping_method_data = None
        if checkout_session.selected_shipping_method:
            shipping_method_data = ShippingMethodSerializer(
                checkout_session.selected_shipping_method
            ).data
        
        return Response({
            'session_token': checkout_session.session_token,
            'status': checkout_session.status,
            'items': cart_items,
            'currency': currency,
            'shipping_address': checkout_session.shipping_address,
            'billing_address': checkout_session.billing_address,
            'shipping_method': shipping_method_data,
            'shipping_costs': {
                'cost_usd': str(checkout_session.shipping_cost_usd),
                'cost_zwl': str(checkout_session.shipping_cost_zwl),
                'cost_zar': str(checkout_session.shipping_cost_zar),
            },
            'promo_code': checkout_session.promo_code,
            'discounts': {
                'discount_amount_usd': str(checkout_session.discount_amount_usd),
                'discount_amount_zwl': str(checkout_session.discount_amount_zwl),
                'discount_amount_zar': str(checkout_session.discount_amount_zar),
            },
            'subtotals': {
                'subtotal_usd': str(subtotals['subtotal_usd']),
                'subtotal_zwl': str(subtotals['subtotal_zwl']),
                'subtotal_zar': str(subtotals['subtotal_zar']),
            },
            'totals': {
                'total_usd': str(totals['total_usd']),
                'total_zwl': str(totals['total_zwl']),
                'total_zar': str(totals['total_zar']),
            }
        }, status=status.HTTP_200_OK)


class CreateOrderView(APIView):
    """
    Create order from checkout session.
    
    POST /api/checkout/create-order/
    Final validation and order creation. Calls cart app's order creation logic.
    """
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_token = serializer.validated_data['session_token']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            checkout_session = CheckoutSession.objects.select_for_update().get(
                session_token=session_token
            )
        except CheckoutSession.DoesNotExist:
            return Response({
                'error': 'Invalid session token'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if checkout_session.is_expired():
            return Response({
                'error': 'Checkout session has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all steps completed
        if checkout_session.status != 'payment_selected':
            return Response({
                'error': 'Please complete all checkout steps first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent duplicate order creation
        if checkout_session.order:
            return Response({
                'error': 'Order already created for this session',
                'order': checkout_session.order.order_number
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order using cart app service
        try:
            order = cart_services.create_order_from_checkout_session(checkout_session, notes)
        except Exception as e:
            return Response({
                'error': f'Failed to create order: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update session
        checkout_session.order = order
        checkout_session.status = 'order_created'
        checkout_session.save()
        
        # Create payment transaction
        currency = checkout_session.cart_data.get('currency', 'USD')
        total_amount = order.get_total()
        
        payment_transaction = PaymentTransaction.objects.create(
            order=order,
            payment_method='payfast',
            amount=total_amount,
            currency=currency,
            status='pending'
        )
        
        # Prepare PayFast payment
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
        return_url = f"{frontend_url}/checkout/success?order={order.order_number}"
        cancel_url = f"{frontend_url}/checkout/cancel?session={session_token}"
        notify_url = f"{request.build_absolute_uri('/api/checkout/payment/callback/')}"
        
        payfast_data = PayFastService.initiate_payment(
            order,
            return_url,
            cancel_url,
            notify_url
        )
        
        # Update payment transaction with PayFast payment ID if available
        if 'payment_data' in payfast_data and 'pf_payment_id' in payfast_data['payment_data']:
            payment_transaction.payfast_payment_id = payfast_data['payment_data']['pf_payment_id']
            payment_transaction.save()
        
        return Response({
            'order': {
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'total': str(total_amount),
                'currency': currency
            },
            'payment_transaction': {
                'transaction_id': payment_transaction.transaction_id,
                'status': payment_transaction.status
            },
            'payment': {
                'payment_url': payfast_data['payment_url'],
                'payment_data': payfast_data['payment_data'],
                'method': 'payfast'
            }
        }, status=status.HTTP_201_CREATED)


class PaymentCallbackView(APIView):
    """
    Handle PayFast payment callback/webhook.
    
    POST /api/checkout/payment/callback/
    Updates PaymentTransaction and Order status.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # PayFast sends data as form data
        data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
        
        # Process payment callback
        result = PayFastService.process_payment_callback(data)
        
        if not result['valid']:
            return Response({
                'error': result.get('error', 'Invalid payment callback')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order_number = result.get('order_number')
        payment_status = result.get('payment_status')
        payfast_payment_id = result.get('payfast_payment_id')
        
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update payment transaction
        payment_transaction = PaymentTransaction.objects.filter(
            order=order
        ).order_by('-created_at').first()
        
        if payment_transaction:
            payment_transaction.payfast_payment_id = payfast_payment_id
            payment_transaction.payfast_data = result.get('data', {})
            
            # Update status based on PayFast response
            if payment_status == 'complete':
                payment_transaction.status = 'completed'
                order.payment_status = 'paid'
                order.status = 'processing'
            elif payment_status == 'failed':
                payment_transaction.status = 'failed'
                order.payment_status = 'failed'
            elif payment_status == 'cancelled':
                payment_transaction.status = 'cancelled'
            
            payment_transaction.save()
            order.save()
        
        # Send confirmation email (implement as needed)
        # send_order_confirmation_email(order)
        
        return Response({
            'status': 'success',
            'order_number': order_number,
            'payment_status': payment_status
        }, status=status.HTTP_200_OK)
