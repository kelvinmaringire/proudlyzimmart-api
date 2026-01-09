# Generated manually for manufacturers app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailimages', '0027_image_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('short_description', models.CharField(blank=True, help_text='Brief description for listings', max_length=500)),
                ('description', models.TextField(help_text='Full company biography/description')),
                ('email', models.EmailField(blank=True, help_text='Contact email')),
                ('phone', models.CharField(blank=True, help_text='Contact phone number', max_length=20)),
                ('address', models.TextField(blank=True, help_text='Street address')),
                ('city', models.CharField(blank=True, help_text='City', max_length=100)),
                ('province', models.CharField(blank=True, help_text='Province (e.g., Harare, Bulawayo, Midlands)', max_length=100)),
                ('country', models.CharField(default='Zimbabwe', help_text='Country', max_length=100)),
                ('website', models.URLField(blank=True, help_text='Company website URL')),
                ('facebook_url', models.URLField(blank=True, help_text='Facebook page URL')),
                ('instagram_url', models.URLField(blank=True, help_text='Instagram profile URL')),
                ('twitter_url', models.URLField(blank=True, help_text='Twitter/X profile URL')),
                ('linkedin_url', models.URLField(blank=True, help_text='LinkedIn company page URL')),
                ('is_active', models.BooleanField(default=True, help_text='Manufacturer is active and visible')),
                ('is_verified', models.BooleanField(default=False, help_text='Manufacturer is verified by ProudlyZimmart')),
                ('is_featured', models.BooleanField(default=False, help_text='Feature this manufacturer prominently')),
                ('meta_title', models.CharField(blank=True, help_text='SEO meta title', max_length=255)),
                ('meta_description', models.TextField(blank=True, help_text='SEO meta description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('logo', models.ForeignKey(blank=True, help_text='Company logo', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manufacturer_logos', to='wagtailimages.image')),
            ],
            options={
                'verbose_name': 'Manufacturer',
                'verbose_name_plural': 'Manufacturers',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='manufacturer',
            index=models.Index(fields=['slug'], name='manufacturer_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturer',
            index=models.Index(fields=['is_active', 'is_featured'], name='manufacturer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturer',
            index=models.Index(fields=['province', 'city'], name='manufacturer_location_idx'),
        ),
    ]

