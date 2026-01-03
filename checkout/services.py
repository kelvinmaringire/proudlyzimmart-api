"""
Services for checkout app.
Handles shipping rate calculation and PayFast payment integration.
"""
import requests
import hashlib
import hmac
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Optional

from .models import ShippingMethod
from products.models import Product, ProductVariation


class ShippingRateService:
    """Service for calculating shipping rates."""
    
    @staticmethod
    def calculate_shipping_rates(
        address: Dict,
        cart_items: List[Dict],
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Main entry point for shipping rate calculation.
        Returns list of available shipping methods with costs.
        """
        # Calculate total weight and dimensions from cart items
        total_weight = Decimal('0.00')
        dimensions = {
            'length': Decimal('0.00'),
            'width': Decimal('0.00'),
            'height': Decimal('0.00'),
        }
        
        for item in cart_items:
            product_id = item.get('product_id')
            variation_id = item.get('variation_id')
            quantity = item.get('quantity', 1)
            
            try:
                product = Product.objects.get(pk=product_id)
                variation = None
                if variation_id:
                    try:
                        variation = ProductVariation.objects.get(
                            pk=variation_id,
                            product=product
                        )
                    except ProductVariation.DoesNotExist:
                        pass
                
                # Get weight (default to 0.5kg if not specified)
                weight = getattr(product, 'weight', Decimal('0.5'))
                if weight:
                    total_weight += Decimal(str(weight)) * quantity
                else:
                    total_weight += Decimal('0.5') * quantity
                
                # Get dimensions (default if not specified)
                length = getattr(product, 'length', Decimal('10'))
                width = getattr(product, 'width', Decimal('10'))
                height = getattr(product, 'height', Decimal('10'))
                
                if length and width and height:
                    dimensions['length'] = max(dimensions['length'], Decimal(str(length)))
                    dimensions['width'] = max(dimensions['width'], Decimal(str(width)))
                    dimensions['height'] += Decimal(str(height)) * quantity
                
            except Product.DoesNotExist:
                continue
        
        # Ensure minimum weight
        if total_weight < Decimal('0.1'):
            total_weight = Decimal('0.1')
        
        # Get all active shipping methods
        shipping_methods = ShippingMethod.objects.filter(is_active=True).order_by('display_order')
        
        rates = []
        for method in shipping_methods:
            try:
                if method.api_enabled:
                    # Try API-based calculation
                    rate = ShippingRateService._get_api_rate(
                        method, address, total_weight, dimensions, currency
                    )
                else:
                    # Use manual rates
                    rate = ShippingRateService._get_manual_rate(
                        method, address, total_weight, currency
                    )
                
                if rate:
                    rates.append({
                        'shipping_method': method,
                        'cost_usd': rate.get('cost_usd', Decimal('0.00')),
                        'cost_zwl': rate.get('cost_zwl', Decimal('0.00')),
                        'cost_zar': rate.get('cost_zar', Decimal('0.00')),
                        'estimated_days_min': method.estimated_days_min,
                        'estimated_days_max': method.estimated_days_max,
                        'method': method.code,
                    })
            except Exception as e:
                # Log error but continue with other methods
                print(f"Error calculating rate for {method.code}: {str(e)}")
                continue
        
        return rates
    
    @staticmethod
    def _get_api_rate(
        method: ShippingMethod,
        address: Dict,
        weight: Decimal,
        dimensions: Dict,
        currency: str
    ) -> Optional[Dict]:
        """Get rate from API based on provider."""
        provider = method.provider
        
        if provider == 'courier_guy':
            return ShippingRateService._get_courier_guy_rates(
                method, address, weight, dimensions, currency
            )
        elif provider == 'dhl':
            return ShippingRateService._get_dhl_rates(
                method, address, weight, dimensions, currency
            )
        elif provider == 'pep_paxi':
            return ShippingRateService._get_pep_paxi_rates(
                method, address, weight, currency
            )
        
        return None
    
    @staticmethod
    def _get_courier_guy_rates(
        method: ShippingMethod,
        address: Dict,
        weight: Decimal,
        dimensions: Dict,
        currency: str
    ) -> Optional[Dict]:
        """Get rates from The Courier Guy API."""
        api_config = method.api_config or {}
        api_key = api_config.get('api_key')
        api_url = api_config.get('api_url', 'https://api.thecourierguy.co.za/v1/rates')
        
        if not api_key:
            return None
        
        try:
            # Prepare request data
            data = {
                'origin': {
                    'city': 'Harare',  # Default origin
                    'country': 'Zimbabwe'
                },
                'destination': {
                    'city': address.get('city', ''),
                    'postal_code': address.get('postal_code', ''),
                    'country': address.get('country', 'Zimbabwe')
                },
                'weight': float(weight),
                'dimensions': {
                    'length': float(dimensions.get('length', 10)),
                    'width': float(dimensions.get('width', 10)),
                    'height': float(dimensions.get('height', 10))
                }
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Extract rate from response (adjust based on actual API response)
                rate_amount = Decimal(str(result.get('rate', 0)))
                
                # Convert to multi-currency (simplified - adjust based on actual rates)
                return {
                    'cost_usd': rate_amount,
                    'cost_zwl': rate_amount * Decimal('1.5'),  # Example conversion
                    'cost_zar': rate_amount * Decimal('18'),  # Example conversion
                }
        except Exception as e:
            print(f"Courier Guy API error: {str(e)}")
        
        return None
    
    @staticmethod
    def _get_dhl_rates(
        method: ShippingMethod,
        address: Dict,
        weight: Decimal,
        dimensions: Dict,
        currency: str
    ) -> Optional[Dict]:
        """Get rates from DHL API."""
        api_config = method.api_config or {}
        api_key = api_config.get('api_key')
        api_url = api_config.get('api_url', 'https://api.dhl.com/rate')
        
        if not api_key:
            return None
        
        try:
            # Prepare request data (adjust based on DHL API requirements)
            data = {
                'origin': {
                    'city': 'Harare',
                    'country': 'ZW'
                },
                'destination': {
                    'city': address.get('city', ''),
                    'postal_code': address.get('postal_code', ''),
                    'country': address.get('country', 'ZW')
                },
                'weight': float(weight),
                'dimensions': {
                    'length': float(dimensions.get('length', 10)),
                    'width': float(dimensions.get('width', 10)),
                    'height': float(dimensions.get('height', 10))
                }
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                rate_amount = Decimal(str(result.get('rate', 0)))
                
                return {
                    'cost_usd': rate_amount,
                    'cost_zwl': rate_amount * Decimal('1.5'),
                    'cost_zar': rate_amount * Decimal('18'),
                }
        except Exception as e:
            print(f"DHL API error: {str(e)}")
        
        return None
    
    @staticmethod
    def _get_pep_paxi_rates(
        method: ShippingMethod,
        address: Dict,
        weight: Decimal,
        currency: str
    ) -> Optional[Dict]:
        """Get rates from Pep Paxi API."""
        api_config = method.api_config or {}
        api_key = api_config.get('api_key')
        api_url = api_config.get('api_url', 'https://api.peppaxi.co.za/v1/rates')
        
        if not api_key:
            return None
        
        try:
            data = {
                'origin': 'Harare',
                'destination': address.get('city', ''),
                'weight': float(weight)
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                rate_amount = Decimal(str(result.get('rate', 0)))
                
                return {
                    'cost_usd': rate_amount,
                    'cost_zwl': rate_amount * Decimal('1.5'),
                    'cost_zar': rate_amount * Decimal('18'),
                }
        except Exception as e:
            print(f"Pep Paxi API error: {str(e)}")
        
        return None
    
    @staticmethod
    def _get_manual_rate(
        method: ShippingMethod,
        address: Dict,
        weight: Decimal,
        currency: str
    ) -> Optional[Dict]:
        """Get rate from manual rates configuration."""
        manual_rates = method.manual_rates or {}
        country = address.get('country', 'Zimbabwe')
        
        # Get rates for country
        country_rates = manual_rates.get(country, {})
        if not country_rates:
            # Fallback to default rates
            country_rates = manual_rates.get('default', {})
        
        if not country_rates:
            return None
        
        # Find matching weight range
        weight_float = float(weight)
        rate = None
        
        # Sort weight ranges
        weight_ranges = sorted(
            country_rates.items(),
            key=lambda x: float(x[0].split('-')[0]) if '-' in x[0] else float(x[0])
        )
        
        for weight_range, price in weight_ranges:
            if '-' in weight_range:
                min_weight, max_weight = map(float, weight_range.split('-'))
                if min_weight <= weight_float <= max_weight:
                    rate = Decimal(str(price))
                    break
            else:
                # Single weight threshold
                threshold = float(weight_range)
                if weight_float <= threshold:
                    rate = Decimal(str(price))
                    break
        
        # Use highest rate if no match found
        if rate is None and weight_ranges:
            rate = Decimal(str(weight_ranges[-1][1]))
        
        if rate is None:
            return None
        
        # Convert to multi-currency (simplified)
        return {
            'cost_usd': rate,
            'cost_zwl': rate * Decimal('1.5'),
            'cost_zar': rate * Decimal('18'),
        }


class PayFastService:
    """Service for PayFast payment integration."""
    
    @staticmethod
    def initiate_payment(
        order,
        return_url: str,
        cancel_url: str,
        notify_url: str
    ) -> Dict:
        """
        Create PayFast payment and return payment URL and parameters.
        Based on PayFast documentation: https://developers.payfast.co.za/docs
        """
        from django.conf import settings
        
        # Get PayFast settings
        merchant_id = getattr(settings, 'PAYFAST_MERCHANT_ID', '')
        merchant_key = getattr(settings, 'PAYFAST_MERCHANT_KEY', '')
        passphrase = getattr(settings, 'PAYFAST_PASSPHRASE', '')
        sandbox = getattr(settings, 'PAYFAST_SANDBOX', True)
        
        if sandbox:
            payfast_url = 'https://sandbox.payfast.co.za/eng/process'
        else:
            payfast_url = 'https://www.payfast.co.za/eng/process'
        
        # Prepare payment data
        payment_data = {
            'merchant_id': merchant_id,
            'merchant_key': merchant_key,
            'return_url': return_url,
            'cancel_url': cancel_url,
            'notify_url': notify_url,
            'name_first': order.shipping_first_name,
            'name_last': order.shipping_last_name,
            'email_address': order.shipping_email,
            'cell_number': order.shipping_phone,
            'm_payment_id': order.order_number,
            'amount': str(order.get_total()),
            'item_name': f'Order {order.order_number}',
            'currency': order.currency,
        }
        
        # Remove empty values
        payment_data = {k: v for k, v in payment_data.items() if v}
        
        # Generate signature
        signature_string = '&'.join([f'{k}={v}' for k, v in sorted(payment_data.items())])
        if passphrase:
            signature_string = f'{signature_string}&passphrase={passphrase}'
        
        signature = hashlib.md5(signature_string.encode()).hexdigest()
        payment_data['signature'] = signature
        
        return {
            'payment_url': payfast_url,
            'payment_data': payment_data,
            'signature': signature
        }
    
    @staticmethod
    def verify_payment_signature(data: Dict) -> bool:
        """Verify PayFast callback signature."""
        from django.conf import settings
        
        passphrase = getattr(settings, 'PAYFAST_PASSPHRASE', '')
        
        # Get signature from data
        received_signature = data.pop('signature', '')
        
        # Recreate signature string
        signature_string = '&'.join([f'{k}={v}' for k, v in sorted(data.items())])
        if passphrase:
            signature_string = f'{signature_string}&passphrase={passphrase}'
        
        calculated_signature = hashlib.md5(signature_string.encode()).hexdigest()
        
        return received_signature == calculated_signature
    
    @staticmethod
    def process_payment_callback(data: Dict) -> Dict:
        """
        Process PayFast webhook/callback.
        Returns payment status and order update info.
        """
        # Verify signature
        if not PayFastService.verify_payment_signature(data.copy()):
            return {
                'valid': False,
                'error': 'Invalid signature'
            }
        
        payment_status = data.get('payment_status', '').lower()
        pf_payment_id = data.get('pf_payment_id', '')
        m_payment_id = data.get('m_payment_id', '')  # Order number
        
        return {
            'valid': True,
            'payment_status': payment_status,
            'payfast_payment_id': pf_payment_id,
            'order_number': m_payment_id,
            'data': data
        }

