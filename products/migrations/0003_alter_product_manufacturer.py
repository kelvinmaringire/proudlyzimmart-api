# Generated manually - Update Product.manufacturer from CharField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


def migrate_manufacturer_data(apps, schema_editor):
    """
    Data migration: Convert existing manufacturer CharField values to Manufacturer instances.
    """
    Manufacturer = apps.get_model('manufacturers', 'Manufacturer')
    Product = apps.get_model('products', 'Product')
    
    # Get all unique manufacturer names from products
    manufacturer_names = Product.objects.exclude(
        manufacturer__isnull=True
    ).exclude(
        manufacturer=''
    ).values_list('manufacturer', flat=True).distinct()
    
    # Create Manufacturer instances for each unique name
    manufacturer_map = {}
    for name in manufacturer_names:
        if name and name.strip():
            # Create manufacturer if it doesn't exist
            manufacturer, created = Manufacturer.objects.get_or_create(
                name=name.strip(),
                defaults={
                    'description': f'Manufacturer: {name.strip()}',
                    'is_active': True,
                }
            )
            manufacturer_map[name] = manufacturer
    
    # Update products to use ForeignKey
    for product in Product.objects.exclude(manufacturer__isnull=True).exclude(manufacturer=''):
        manufacturer_name = product.manufacturer
        if manufacturer_name in manufacturer_map:
            product.manufacturer_new = manufacturer_map[manufacturer_name]
            product.save()


def reverse_migrate_manufacturer_data(apps, schema_editor):
    """
    Reverse migration: Convert Manufacturer ForeignKey back to CharField.
    Note: In reverse, manufacturer_new (ForeignKey) exists and manufacturer (CharField) was just added back.
    """
    Manufacturer = apps.get_model('manufacturers', 'Manufacturer')
    Product = apps.get_model('products', 'Product')
    
    # At this point in reverse, manufacturer_new (ForeignKey) exists
    # and manufacturer (CharField) was just added back
    for product in Product.objects.exclude(manufacturer_new__isnull=True):
        if hasattr(product, 'manufacturer_new_id') and product.manufacturer_new_id:
            try:
                manufacturer_obj = Manufacturer.objects.get(id=product.manufacturer_new_id)
                product.manufacturer = manufacturer_obj.name
                product.save(update_fields=['manufacturer'])
            except Manufacturer.DoesNotExist:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_productimage_image_alter_productimage_product_and_more'),
        ('manufacturers', '0001_initial'),
    ]

    operations = [
        # Add new ForeignKey field (temporarily nullable)
        migrations.AddField(
            model_name='product',
            name='manufacturer_new',
            field=models.ForeignKey(
                blank=True,
                help_text='Manufacturer/Company supplying this product',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to='manufacturers.manufacturer'
            ),
        ),
        # Migrate data
        migrations.RunPython(migrate_manufacturer_data, reverse_migrate_manufacturer_data),
        # Remove old CharField
        migrations.RemoveField(
            model_name='product',
            name='manufacturer',
        ),
        # Rename new field to manufacturer
        migrations.RenameField(
            model_name='product',
            old_name='manufacturer_new',
            new_name='manufacturer',
        ),
    ]

