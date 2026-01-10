# Generated migration to update ManufacturerSubmission model
# - Add address field
# - Remove Zimbabwe default from country field
# - Update province help text

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturers', '0003_alter_phone_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='manufacturersubmission',
            name='address',
            field=models.TextField(blank=True, help_text='Street address'),
        ),
        migrations.AlterField(
            model_name='manufacturersubmission',
            name='country',
            field=models.CharField(blank=True, help_text='Country', max_length=100),
        ),
        migrations.AlterField(
            model_name='manufacturersubmission',
            name='province',
            field=models.CharField(blank=True, help_text='Province/State/Region', max_length=100),
        ),
    ]


