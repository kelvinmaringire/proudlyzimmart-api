# Import/Export Guide for Products and Categories

This guide explains how to use the CSV/Excel import/export functionality integrated with Wagtail ModelAdmin.

## Installation

1. Install the required package:
```bash
pip install django-import-export
```

2. The package is already added to `requirements.txt` and `INSTALLED_APPS`.

3. Run migrations (if needed):
```bash
python manage.py migrate
```

## Features

- **Export Products/Categories** to CSV or Excel format
- **Import Products/Categories** from CSV or Excel files
- **Automatic foreign key resolution** (category by name, product_type by type)
- **SKU-based updates** - Products with existing SKUs are updated instead of duplicated
- **Error handling** with clear feedback messages
- **Support for all product fields** including multi-currency pricing

## Usage

### Exporting Data

1. Navigate to **Products** or **Categories** in the Wagtail admin (`/admin/`)
2. Click the **"Export"** button in the top-right corner
3. Choose your preferred format:
   - **Export as CSV** - For spreadsheet applications
   - **Export as Excel** - For Microsoft Excel
4. The file will download automatically

### Importing Data

1. Navigate to **Products** or **Categories** in the Wagtail admin
2. Click the **"Import"** button in the top-right corner
3. Select your file format (CSV or Excel)
4. Choose the file to import
5. Click **"Import"**
6. Review the success/error messages

## CSV/Excel File Format

### Product Import Format

Required fields:
- `sku` - Unique product identifier (used for updates)
- `name` - Product name
- `product_type` - Product type (e.g., 'ready_to_buy', 'collect', 'enquire', 'promotional')

Optional fields:
- `slug` - URL slug (auto-generated if not provided)
- `description` - Full product description
- `short_description` - Short description (max 500 chars)
- `category` - Category name (must exist)
- `brand` - Brand name
- `manufacturer` - Manufacturer name
- `is_proudlyzimmart_brand` - Boolean (true/false, 1/0, yes/no)
- `price_usd`, `price_zwl`, `price_zar` - Regular prices
- `sale_price_usd`, `sale_price_zwl`, `sale_price_zar` - Sale prices
- `stock_quantity` - Stock quantity (integer)
- `low_stock_threshold` - Low stock alert threshold
- `track_stock` - Boolean
- `in_stock` - Boolean
- `is_active` - Boolean
- `is_featured` - Boolean
- `is_standard` - Boolean
- `weight` - Weight in kg (decimal)
- `dimensions` - Dimensions string
- `meta_title` - SEO meta title
- `meta_description` - SEO meta description
- `tags` - Comma-separated tags

### Category Import Format

Required fields:
- `slug` - Unique category identifier (used for updates)
- `name` - Category name

Optional fields:
- `description` - Category description
- `parent` - Parent category name (must exist)
- `is_active` - Boolean
- `order` - Display order (integer)

## Examples

### Example Product CSV

```csv
sku,name,product_type,category,brand,price_usd,stock_quantity,is_active
PROD001,Example Product,ready_to_buy,Electronics,Brand Name,99.99,50,true
PROD002,Another Product,collect,Fashion,Another Brand,149.99,25,true
```

### Example Category CSV

```csv
slug,name,description,parent,is_active,order
electronics,Electronics,Electronic products,,true,1
phones,Phones,Mobile phones,Electronics,true,2
```

## Foreign Key Resolution

### Products

- **Category**: Looked up by `name` field
  - If category doesn't exist, import will fail with an error message
  - Create categories first before importing products
  
- **Product Type**: Looked up by `type` field (e.g., 'ready_to_buy')
  - Available types: `ready_to_buy`, `collect`, `enquire`, `promotional`
  - If type doesn't exist, import will fail with an error message

### Categories

- **Parent Category**: Looked up by `name` field
  - If parent doesn't exist, import will fail
  - Import parent categories before child categories

## Handling Edge Cases

### Duplicate SKUs

- Products with existing SKUs will be **updated** (not duplicated)
- The `sku` field is used as the unique identifier
- All fields in the import file will update the existing product

### Missing Categories

- If a product references a category that doesn't exist, the import will fail
- **Solution**: Export categories first, or create them manually before importing products
- Error message will indicate which category is missing

### Missing Product Types

- If a product references a product type that doesn't exist, the import will fail
- **Solution**: Create product types in the admin first
- Available types are listed in the error message

### Invalid Data Types

- Boolean fields accept: `true`, `false`, `1`, `0`, `yes`, `no`
- Decimal fields must be valid numbers
- Integer fields must be whole numbers
- Invalid data will cause row-level errors

## Error Messages

The import process provides detailed error messages:

- **Row-level errors**: Shows which row has an error and what the problem is
- **Summary**: Shows how many records were imported, updated, or skipped
- **Validation errors**: Clear messages about missing foreign keys or invalid data

## Best Practices

1. **Export first**: Always export existing data before making changes
2. **Test with small files**: Test imports with a few records first
3. **Create dependencies first**: Import categories and product types before products
4. **Backup data**: Always backup your database before bulk imports
5. **Validate data**: Check your CSV/Excel file for errors before importing
6. **Use SKUs consistently**: Use the same SKU format across imports

## Troubleshooting

### Import fails with "Category not found"

- Check that the category name in your CSV exactly matches an existing category
- Export categories first to see the correct names
- Create missing categories manually before importing

### Import fails with "Product type not found"

- Check that you're using the correct product type value
- Available types: `ready_to_buy`, `collect`, `enquire`, `promotional`
- Create product types in the admin if they don't exist

### Boolean fields not working

- Use `true`/`false`, `1`/`0`, or `yes`/`no` (case-insensitive)
- Empty values default to `false`

### Prices not importing correctly

- Ensure decimal values use a period (.) as the decimal separator
- Do not include currency symbols in price fields
- Example: `99.99` not `$99.99` or `99,99`

## Technical Details

### Resource Classes

- `ProductResource` - Handles Product import/export
- `CategoryResource` - Handles Category import/export

### File Locations

- Resources: `products/resources.py`
- Admin integration: `products/wagtail_hooks.py`
- Templates: `products/templates/wagtail_modeladmin/products/`

### URL Patterns

- Import: `/admin/products/products/import/` (for Products)
- Export: `/admin/products/products/export/?format=csv` (for Products)
- Similar patterns for Categories

## Support

For issues or questions:
1. Check error messages in the admin interface
2. Review this guide for common issues
3. Check the Django/Wagtail logs for detailed error information

