from django.db import migrations, models
import django.db.models.deletion
from wagtail.fields import RichTextField


FULL_RICH_TEXT_FEATURES = [
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "bold",
    "italic",
    "ol",
    "ul",
    "hr",
    "link",
    "document-link",
    "image",
    "embed",
    "code",
    "blockquote",
    "superscript",
    "subscript",
    "strikethrough",
]


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("wagtailcore", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoreSiteSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site",
                    models.OneToOneField(
                        db_index=True,
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="wagtailcore.site",
                        unique=True,
                    ),
                ),
                ("privacy_policy", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("terms_and_conditions", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("return_refund_policy", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("faqs", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("about_us", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("announcement_enabled", models.BooleanField(default=False)),
                ("announcement_bar_text", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=50)),
                ("contact_address", RichTextField(blank=True, features=FULL_RICH_TEXT_FEATURES)),
                ("facebook_url", models.URLField(blank=True)),
                ("instagram_url", models.URLField(blank=True)),
                ("x_url", models.URLField(blank=True)),
                ("linkedin_url", models.URLField(blank=True)),
                ("tiktok_url", models.URLField(blank=True)),
                ("youtube_url", models.URLField(blank=True)),
                ("whatsapp_url", models.URLField(blank=True)),
            ],
            options={
                "verbose_name": "Core Site Settings",
            },
        ),
    ]
