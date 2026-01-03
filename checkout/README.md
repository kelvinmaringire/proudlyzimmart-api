# Checkout App - Multi-Step Checkout API

A comprehensive headless checkout API app that orchestrates the checkout process from cart to order creation. Supports both guest and authenticated checkout flows.

## Overview

The checkout app handles:
- **Address Collection** - Shipping and billing addresses
- **Shipping Method Selection** - API-integrated and manual shipping rate calculation
- **Payment Processing** - PayFast payment gateway integration
- **Order Creation** - Orchestrates order creation in the cart app

## Architecture

### Models

1. **CheckoutSession** - Token-based session tracking (SPA-compatible)
   - Tracks checkout state through multi-step flow
   - Supports both guest and authenticated users
   - Expires after configured time (default: 30 minutes)

2. **ShippingMethod** - Configured shipping methods
   - Supports multiple providers (The Courier Guy, DHL, Pep Paxi, Manual)
   - API-enabled or manual rate calculation
   - Configurable delivery estimates

3. **PaymentTransaction** - Payment tracking
   - Links to Order after creation
   - Tracks PayFast payment status
   - Stores payment callback data

### API Endpoints

#### 1. Initialize Checkout
```
POST /api/checkout/init/
```
Creates a checkout session and validates cart items.

**Request:**
```json
{
  "items": [
    {
      "product_id": 1,
      "variation_id": null,
      "quantity": 2
    }
  ],
  "currency": "USD",
  "promo_code": "DISCOUNT10"
}
```

**Response:**
```json
{
  "session_token": "abc123...",
  "status": "initiated",
  "expires_at": "2024-01-01T12:00:00Z",
  "subtotals": {
    "subtotal_usd": "100.00",
    "subtotal_zwl": "150.00",
    "subtotal_zar": "1800.00"
  },
  "discounts": {
    "discount_amount_usd": "10.00",
    "discount_amount_zwl": "15.00",
    "discount_amount_zar": "180.00"
  },
  "currency": "USD"
}
```

#### 2. Collect Addresses
```
POST /api/checkout/address/
```
Saves shipping and billing addresses, returns available shipping methods.

**Request:**
```json
{
  "session_token": "abc123...",
  "shipping_address": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+263771234567",
    "address_line1": "123 Main St",
    "address_line2": "",
    "city": "Harare",
    "state": "",
    "postal_code": "0000",
    "country": "Zimbabwe"
  },
  "billing_address": {...},
  "use_billing_as_shipping": false
}
```

**Response:**
```json
{
  "session_token": "abc123...",
  "status": "address_collected",
  "shipping_address": {...},
  "billing_address": {...},
  "available_shipping_methods": [
    {
      "id": 1,
      "name": "The Courier Guy",
      "code": "courier_guy",
      "provider": "courier_guy",
      "cost_usd": "15.00",
      "cost_zwl": "22.50",
      "cost_zar": "270.00",
      "estimated_days_min": 3,
      "estimated_days_max": 5
    }
  ]
}
```

#### 3. Select Shipping Method
```
POST /api/checkout/shipping/
```
Selects shipping method and calculates totals.

**Request:**
```json
{
  "session_token": "abc123...",
  "shipping_method_id": 1
}
```

**Response:**
```json
{
  "session_token": "abc123...",
  "status": "shipping_selected",
  "shipping_method": {...},
  "shipping_costs": {
    "cost_usd": "15.00",
    "cost_zwl": "22.50",
    "cost_zar": "270.00"
  },
  "totals": {
    "subtotal_usd": "100.00",
    "discount_amount_usd": "10.00",
    "shipping_cost_usd": "15.00",
    "total_usd": "105.00"
  }
}
```

#### 4. Select Payment Method
```
POST /api/checkout/payment/
```
Selects payment method (currently only PayFast).

**Request:**
```json
{
  "session_token": "abc123...",
  "payment_method": "payfast"
}
```

#### 5. Review Order
```
GET /api/checkout/review/?session_token=abc123...
```
Returns complete checkout summary before order creation.

#### 6. Create Order
```
POST /api/checkout/create-order/
```
Creates order and returns PayFast payment URL.

**Request:**
```json
{
  "session_token": "abc123...",
  "notes": "Please deliver in the morning"
}
```

**Response:**
```json
{
  "order": {
    "order_number": "ABC123XYZ",
    "status": "pending",
    "payment_status": "pending",
    "total": "105.00",
    "currency": "USD"
  },
  "payment_transaction": {
    "transaction_id": "TX123...",
    "status": "pending"
  },
  "payment": {
    "payment_url": "https://sandbox.payfast.co.za/eng/process",
    "payment_data": {...},
    "method": "payfast"
  }
}
```

#### 7. Payment Callback
```
POST /api/checkout/payment/callback/
```
Handles PayFast webhook/return URL. Updates order and payment status.

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Checkout Session
CHECKOUT_SESSION_EXPIRY_MINUTES=30

# PayFast
PAYFAST_MERCHANT_ID=your_merchant_id
PAYFAST_MERCHANT_KEY=your_merchant_key
PAYFAST_PASSPHRASE=your_passphrase
PAYFAST_SANDBOX=True

# Shipping APIs (optional)
COURIER_GUY_API_KEY=your_api_key
COURIER_GUY_API_URL=https://api.thecourierguy.co.za/v1/rates
DHL_API_KEY=your_api_key
DHL_API_URL=https://api.dhl.com/rate
PEP_PAXI_API_KEY=your_api_key
PEP_PAXI_API_URL=https://api.peppaxi.co.za/v1/rates
```

### Shipping Methods Setup

Configure shipping methods in Django admin:

1. Go to `/admin/checkout/shippingmethod/`
2. Create shipping methods:
   - **Name**: Display name (e.g., "The Courier Guy")
   - **Code**: Unique code (e.g., "courier_guy")
   - **Provider**: Select provider type
   - **API Enabled**: Check if using API integration
   - **API Config**: JSON config with API keys
   - **Manual Rates**: JSON structure for manual rates

**Manual Rates JSON Example:**
```json
{
  "Zimbabwe": {
    "0-1": "10.00",
    "1-5": "15.00",
    "5-10": "20.00",
    "10+": "25.00"
  },
  "default": {
    "0-1": "15.00",
    "1-5": "25.00",
    "5-10": "35.00",
    "10+": "50.00"
  }
}
```

## Data Flow

```
Frontend SPA
    ↓
1. POST /api/checkout/init/ (cart validation)
    ↓
2. POST /api/checkout/address/ (address collection)
    ↓
3. POST /api/checkout/shipping/ (shipping method + rates)
    ↓
4. POST /api/checkout/payment/ (payment method selection)
    ↓
5. GET /api/checkout/review/ (order review)
    ↓
6. POST /api/checkout/create-order/ (create order in cart app)
    ↓
7. Redirect to PayFast payment page
    ↓
8. PayFast callback → POST /api/checkout/payment/callback/
    ↓
9. Update order status, send confirmation email
```

## Guest Checkout

The checkout app fully supports guest checkout:
- Uses token-based sessions (no Django session required)
- `user` field in CheckoutSession can be `None`
- Order creation supports `user=None` for guest orders

## Integration with Cart App

- Order creation logic remains in `cart/services.py`
- Checkout app calls `create_order_from_checkout_session()` function
- Cart app's `CheckoutView` updated to support guest checkout

## Testing

### Test Guest Checkout Flow
1. Initialize checkout without authentication
2. Complete all steps
3. Verify order created with `user=None`

### Test Shipping Rates
1. Configure shipping methods in admin
2. Test API-based rates (if API keys configured)
3. Test manual rates fallback

### Test PayFast Integration
1. Use PayFast sandbox mode for testing
2. Test payment callback handling
3. Verify order status updates

## Notes

- CheckoutSession expires after configured time (default: 30 minutes)
- Shipping rates calculated on-demand when address provided
- Order only created after payment method selection and final review
- PaymentTransaction tracks all payment attempts for an order
- PayFast signature verification ensures payment security

## Dependencies

Add to `requirements.txt`:
```
requests>=2.31.0  # For API calls to courier companies and PayFast
```

## Admin Interface

All models are registered in Django admin:
- **ShippingMethod** - Configure shipping methods and rates
- **PaymentTransaction** - Track payment attempts
- **CheckoutSession** - Debug checkout sessions

