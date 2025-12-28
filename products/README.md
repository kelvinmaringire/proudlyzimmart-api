# Products App - ProudlyZimmart Marketplace

This app provides a comprehensive product management system for the ProudlyZimmart marketplace, supporting multiple product types, categories, variations, reviews, and advanced search capabilities.

## Table of Contents

- [Features](#features)
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Models](#models)
- [API Endpoints](#api-endpoints)
- [Product Types](#product-types)
- [Multi-Currency Support](#multi-currency-support)
- [Usage Examples](#usage-examples)
- [Admin Interface](#admin-interface)

## Features

- ✅ Multi-category product catalog with hierarchical categories
- ✅ Four product types: Ready to Buy, Collect, Enquire, Promotional
- ✅ Multi-currency pricing (USD, ZWL RTGS, ZAR)
- ✅ Product variations (sizes, colors, models)
- ✅ Multiple product images with primary image support
- ✅ Stock tracking and management
- ✅ Customer reviews and ratings
- ✅ Related products / recommendations
- ✅ Advanced search with filters
- ✅ Product filtering by category, price, rating, brand
- ✅ Featured products and sale products
- ✅ SKU generation and management
- ✅ SEO-friendly URLs with slugs

## Overview

The products app implements a complete product management system using:
- **Django REST Framework** - REST API framework
- **django-filter** - Advanced filtering capabilities
- **PostgreSQL** - Database with optimized indexes

### Key Components

- **Product Model** - Main product model with multi-currency pricing
- **Category Model** - Hierarchical category system
- **ProductType Model** - Product type classification
- **ProductVariation Model** - Product variations (sizes, colors, etc.)
- **ProductImage Model** - Multiple images per product
- **Review Model** - Customer reviews and ratings
- **RelatedProduct Model** - Product recommendations

## Project Structure

```
products/
├── __init__.py
├── admin.py          # Admin configuration
├── apps.py           # App configuration
├── models.py         # Product models
├── serializers.py    # DRF serializers
├── services.py       # Business logic layer
├── urls.py           # URL routing
├── views.py          # API views
├── tests.py          # Unit tests
├── migrations/       # Database migrations
└── README.md         # This file
```

## Models

### Category

Hierarchical category system with parent-child relationships.

**Fields:**
- `name` - Category name
- `slug` - URL-friendly slug (auto-generated)
- `description` - Category description
- `parent` - Parent category (for subcategories)
- `image` - Category image
- `is_active` - Active status
- `order` - Display order

**Usage:**
```python
# Create category
category = Category.objects.create(
    name="Electronics",
    description="Electronic products"
)

# Create subcategory
subcategory = Category.objects.create(
    name="Mobile Phones",
    parent=category
)
```

### ProductType

Product type classification system.

**Types:**
- `ready_to_buy` - Products available online and in-store, ready to ship
- `collect` - Products fetched from manufacturer when ordered
- `enquire` - Products requiring inquiry (e.g., agricultural products)
- `promotional` - Products only promoted, not sold

**Usage:**
```python
# Get product type
ready_type = ProductType.objects.get(type='ready_to_buy')
```

### Product

Main product model with comprehensive fields.

**Key Fields:**
- `name` - Product name
- `slug` - URL-friendly slug (auto-generated)
- `sku` - Stock Keeping Unit (auto-generated)
- `description` - Full product description
- `short_description` - Brief description
- `category` - Product category
- `product_type` - Product type
- `brand` - Brand name (must be Zimbabwean)
- `is_proudlyzimmart_brand` - ProudlyZimmart own brand flag
- `price_usd`, `price_zwl`, `price_zar` - Regular prices
- `sale_price_usd`, `sale_price_zwl`, `sale_price_zar` - Sale prices
- `stock_quantity` - Available stock
- `track_stock` - Enable stock tracking
- `in_stock` - Stock availability (auto-calculated)
- `is_active` - Active status
- `is_featured` - Featured product flag
- `average_rating` - Average rating (auto-calculated)
- `review_count` - Number of reviews (auto-calculated)

**Methods:**
- `get_current_price(currency)` - Get current price (sale if available)
- `is_on_sale()` - Check if product is on sale
- `update_rating()` - Update average rating from reviews

**Usage:**
```python
# Create product
product = Product.objects.create(
    name="Zimbabwean Coffee Beans",
    description="Premium Zimbabwean coffee beans",
    category=category,
    product_type=ready_type,
    brand="ZimCoffee Co",
    price_usd=25.00,
    price_zwl=500.00,
    stock_quantity=100,
    is_active=True
)

# Get current price
current_price = product.get_current_price('USD')

# Check if on sale
if product.is_on_sale():
    print("Product is on sale!")
```

### ProductVariation

Product variations for sizes, colors, models, etc.

**Fields:**
- `product` - Parent product
- `name` - Variation name (e.g., "Size", "Color")
- `value` - Variation value (e.g., "Large", "Red")
- `sku` - Variation SKU (auto-generated)
- `price_adjustment_usd/zwl/zar` - Price adjustments
- `stock_quantity` - Stock for this variation

**Usage:**
```python
# Create variation
variation = ProductVariation.objects.create(
    product=product,
    name="Size",
    value="Large",
    price_adjustment_usd=5.00,
    stock_quantity=50
)
```

### ProductImage

Multiple images per product with primary image support.

**Fields:**
- `product` - Parent product
- `image` - Image file
- `alt_text` - Alt text for SEO
- `is_primary` - Primary image flag
- `order` - Display order

**Usage:**
```python
# Upload image
image = ProductImage.objects.create(
    product=product,
    image=image_file,
    alt_text="Zimbabwean Coffee Beans",
    is_primary=True
)
```

### Review

Customer reviews and ratings.

**Fields:**
- `product` - Reviewed product
- `user` - Review author
- `rating` - Rating (1-5)
- `title` - Review title
- `comment` - Review text
- `is_approved` - Admin approval status
- `is_verified_purchase` - Verified purchase flag
- `helpful_count` - Helpful votes count

**Usage:**
```python
# Create review
review = Review.objects.create(
    product=product,
    user=user,
    rating=5,
    title="Excellent coffee!",
    comment="Best coffee I've ever tasted.",
    is_verified_purchase=True
)

# Review automatically updates product rating
```

### RelatedProduct

Product recommendations.

**Fields:**
- `product` - Main product
- `related_product` - Related product
- `order` - Display order

## API Endpoints

### Categories

- `GET /api/products/categories/` - List all categories
- `GET /api/products/categories/<slug>/` - Get category details

### Product Types

- `GET /api/products/types/` - List all product types

### Products

- `GET /api/products/products/` - List all products (with filtering)
- `POST /api/products/products/` - Create product (admin only)
- `GET /api/products/products/<id>/` - Get product details
- `PUT /api/products/products/<id>/` - Update product (admin only)
- `PATCH /api/products/products/<id>/` - Partial update (admin only)
- `DELETE /api/products/products/<id>/` - Delete product (admin only)
- `GET /api/products/products/<id>/variations/` - Get product variations
- `GET /api/products/products/<id>/images/` - Get product images
- `GET /api/products/products/<id>/reviews/` - Get product reviews
- `POST /api/products/products/<id>/add_review/` - Add review (authenticated)
- `GET /api/products/products/<id>/related/` - Get related products
- `GET /api/products/products/featured/` - Get featured products
- `GET /api/products/products/on-sale/` - Get products on sale
- `GET /api/products/products/search/?q=query` - Search products

### Variations

- `GET /api/products/variations/` - List variations (admin only)
- `POST /api/products/variations/` - Create variation (admin only)

### Images

- `GET /api/products/images/` - List images (admin only)
- `POST /api/products/images/` - Upload image (admin only)

### Reviews

- `GET /api/products/reviews/` - List reviews
- `POST /api/products/reviews/` - Create review (authenticated)
- `POST /api/products/reviews/<id>/mark_helpful/` - Mark review helpful

### Search

- `GET /api/products/search/?q=query&category=slug&min_price=100&max_price=500` - Advanced search

## Product Types

### Ready to Buy
Products available online and in-store, ready to ship instantly.

**Characteristics:**
- Must have stock quantity > 0
- Can be purchased immediately
- Ready for shipping

### Collect
Products collected from manufacturer when customer orders.

**Characteristics:**
- Stock may be 0 (collected on order)
- Requires collection time
- Customer notified when ready

### Enquire
Products requiring inquiry about price, quantity, and availability.

**Characteristics:**
- Typically agricultural products
- No direct purchase
- Customer must inquire

### Promotional
Products only promoted, not sold online or offline.

**Characteristics:**
- For marketing purposes only
- No purchase option
- Display only

## Multi-Currency Support

The system supports three currencies:
- **USD** - United States Dollar
- **ZWL RTGS** - Zimbabwean RTGS Dollar
- **ZAR** - South African Rand

**Pricing Fields:**
- Regular prices: `price_usd`, `price_zwl`, `price_zar`
- Sale prices: `sale_price_usd`, `sale_price_zwl`, `sale_price_zar`

**Usage:**
```python
# Set prices
product.price_usd = 25.00
product.price_zwl = 500.00
product.price_zar = 450.00

# Set sale prices
product.sale_price_usd = 20.00
product.sale_price_zwl = 400.00

# Get current price
current_usd = product.get_current_price('USD')  # Returns 20.00 (sale price)
```

## Usage Examples

### List Products with Filters

```bash
# Get all active products
GET /api/products/products/?is_active=true

# Filter by category
GET /api/products/products/?category=electronics

# Filter by price range
GET /api/products/products/?price_usd__gte=10&price_usd__lte=100

# Filter by rating
GET /api/products/products/?average_rating__gte=4

# Filter by brand
GET /api/products/products/?brand=ZimBrand

# Filter by product type
GET /api/products/products/?product_type=ready_to_buy

# Search products
GET /api/products/products/search/?q=coffee&category=food&min_price=10&max_price=50
```

### Create Product

```bash
POST /api/products/products/
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "name": "Zimbabwean Coffee Beans",
  "description": "Premium coffee beans from Zimbabwe",
  "short_description": "Premium coffee",
  "category_id": 1,
  "product_type_id": 1,
  "brand": "ZimCoffee Co",
  "price_usd": 25.00,
  "price_zwl": 500.00,
  "stock_quantity": 100,
  "is_active": true,
  "is_featured": false
}
```

### Add Review

```bash
POST /api/products/products/1/add_review/
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "rating": 5,
  "title": "Excellent product!",
  "comment": "Best coffee I've ever tasted. Highly recommended!"
}
```

### Search Products

```bash
GET /api/products/search/?q=coffee&category=food&min_price=10&max_price=50&min_rating=4&in_stock_only=true
```

## Admin Interface

The admin interface provides comprehensive product management:

- **Category Management** - Create/edit categories with hierarchy
- **Product Management** - Full CRUD operations with inline images and variations
- **Review Management** - Approve/reject reviews
- **Stock Management** - Track stock levels and low stock alerts
- **Image Management** - Upload and manage product images
- **Variation Management** - Manage product variations

### Admin Features

- Bulk actions for products
- Image previews
- Price display with sale indicators
- Stock status indicators
- Review approval workflow
- Autocomplete for related fields

## Notes

- All products must be branded, packaged, and made/assembled in Zimbabwe
- Products must meet standard requirements (`is_standard=True`)
- ProudlyZimmart must have its own products (`is_proudlyzimmart_brand=True`)
- Stock tracking is optional but recommended for Ready to Buy products
- Reviews require admin approval before display
- Product ratings are automatically calculated from approved reviews
- SKUs are auto-generated if not provided
- Slugs are auto-generated from product names

