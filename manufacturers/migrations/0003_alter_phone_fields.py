# Generated manually - Alter phone fields to accept international numbers

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturers', '0002_manufacturersubmission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manufacturer',
            name='phone',
            field=models.CharField(blank=True, help_text='Contact phone number (international format accepted)', max_length=30),
        ),
        migrations.AlterField(
            model_name='manufacturersubmission',
            name='phone',
            field=models.CharField(help_text='Contact phone number (international format accepted)', max_length=30),
        ),
    ]

