from rest_framework import serializers
from rest_framework.fields import CharField
from wagtail.rich_text import expand_db_html

from .models import CoreSiteSettings


class RichTextSerializer(CharField):
    """Serializer for Wagtail RichTextField that expands database HTML."""

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation:
            return expand_db_html(representation)
        return representation


class CoreSiteSettingsSerializer(serializers.ModelSerializer):
    """Serializer for core site settings."""

    privacy_policy = RichTextSerializer()
    terms_and_conditions = RichTextSerializer()
    return_refund_policy = RichTextSerializer()
    faqs = RichTextSerializer()
    about_us = RichTextSerializer()
    announcement_bar_text = RichTextSerializer()
    contact_address = RichTextSerializer()

    class Meta:
        model = CoreSiteSettings
        fields = (
            "privacy_policy",
            "terms_and_conditions",
            "return_refund_policy",
            "faqs",
            "about_us",
            "announcement_enabled",
            "announcement_bar_text",
            "contact_email",
            "contact_phone",
            "contact_address",
            "facebook_url",
            "instagram_url",
            "x_url",
            "linkedin_url",
            "tiktok_url",
            "youtube_url",
            "whatsapp_url",
        )


class ContactSubmissionSerializer(serializers.Serializer):
    """Serializer for contact form submissions."""

    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
