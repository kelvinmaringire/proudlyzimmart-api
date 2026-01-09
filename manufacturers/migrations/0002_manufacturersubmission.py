# Generated manually for ManufacturerSubmission model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ManufacturerSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Contact person name', max_length=255)),
                ('email', models.EmailField(help_text='Contact email address')),
                ('phone', models.CharField(help_text='Contact phone number (international format accepted)', max_length=30)),
                ('company_name', models.CharField(blank=True, help_text='Company/Business name', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Company description and what products/services you offer')),
                ('website', models.URLField(blank=True, help_text='Company website URL')),
                ('city', models.CharField(blank=True, help_text='City', max_length=100)),
                ('province', models.CharField(blank=True, help_text='Province (e.g., Harare, Bulawayo, Midlands)', max_length=100)),
                ('country', models.CharField(default='Zimbabwe', help_text='Country', max_length=100)),
                ('product_types', models.TextField(blank=True, help_text="Types of products you want to sell (e.g., Ready to Buy, Collect, Enquire, Promotional)")),
                ('product_categories', models.TextField(blank=True, help_text="Product categories you're interested in (e.g., Musika, Grombi, Fashani, Technology)")),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('reviewed', 'Reviewed'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', help_text='Submission status', max_length=20)),
                ('admin_notes', models.TextField(blank=True, help_text='Admin notes and review comments')),
                ('reviewed_at', models.DateTimeField(blank=True, help_text='When this submission was reviewed', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewed_by', models.ForeignKey(blank=True, help_text='Admin user who reviewed this submission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Manufacturer Submission',
                'verbose_name_plural': 'Manufacturer Submissions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='manufacturersubmission',
            index=models.Index(fields=['status'], name='manufacturer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturersubmission',
            index=models.Index(fields=['created_at'], name='manufacturer_created_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturersubmission',
            index=models.Index(fields=['email'], name='manufacturer_email_idx'),
        ),
    ]

