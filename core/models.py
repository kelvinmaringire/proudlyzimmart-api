from django.db import models
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
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


@register_setting
class CoreSiteSettings(BaseSiteSetting):
    """Site-wide core content managed via Wagtail Settings."""

    # Policy and informational content
    privacy_policy = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Privacy policy content."
    )
    terms_and_conditions = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Terms and conditions content."
    )
    return_refund_policy = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Return and refund policy content."
    )
    faqs = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Frequently asked questions content."
    )
    about_us = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="About us content."
    )

    # Announcement bar
    announcement_enabled = models.BooleanField(
        default=False,
        help_text="Toggle the announcement bar on/off."
    )
    announcement_bar_text = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Announcement bar text."
    )

    # Contact information
    contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email address."
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary contact phone number."
    )
    contact_address = RichTextField(
        blank=True,
        features=FULL_RICH_TEXT_FEATURES,
        help_text="Contact address or location details."
    )

    # Social links
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("privacy_policy"),
            FieldPanel("terms_and_conditions"),
            FieldPanel("return_refund_policy"),
            FieldPanel("faqs"),
            FieldPanel("about_us"),
        ], heading="Policies & Information"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel("announcement_enabled"),
            ]),
            FieldPanel("announcement_bar_text"),
        ], heading="Announcement Bar"),
        MultiFieldPanel([
            FieldPanel("contact_email"),
            FieldPanel("contact_phone"),
            FieldPanel("contact_address"),
        ], heading="Contact Information"),
        MultiFieldPanel([
            FieldPanel("facebook_url"),
            FieldPanel("instagram_url"),
            FieldPanel("x_url"),
            FieldPanel("linkedin_url"),
            FieldPanel("tiktok_url"),
            FieldPanel("youtube_url"),
            FieldPanel("whatsapp_url"),
        ], heading="Social Links"),
    ]

    class Meta:
        verbose_name = "Core Site Settings"
