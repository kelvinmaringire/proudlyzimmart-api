"""
Manufacturer models for ProudlyZimmart marketplace.
Handles manufacturer/company profiles (auto-biography) of suppliers.
"""
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, FieldRowPanel
)
from wagtail.images.models import Image


class Manufacturer(models.Model):
    """Manufacturer/Company profile model - auto-biography of suppliers to ProudlyZimmart."""
    
    # Basic Information
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief description for listings"
    )
    description = models.TextField(
        help_text="Full company biography/description"
    )
    logo = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manufacturer_logos',
        help_text="Company logo"
    )
    
    # Contact Details
    email = models.EmailField(
        blank=True,
        help_text="Contact email"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )
    address = models.TextField(
        blank=True,
        help_text="Street address"
    )
    
    # Location (Zimbabwe-focused)
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City"
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        help_text="Province (e.g., Harare, Bulawayo, Midlands)"
    )
    country = models.CharField(
        max_length=100,
        default="Zimbabwe",
        help_text="Country"
    )
    
    # Online Presence
    website = models.URLField(
        blank=True,
        help_text="Company website URL"
    )
    facebook_url = models.URLField(
        blank=True,
        help_text="Facebook page URL"
    )
    instagram_url = models.URLField(
        blank=True,
        help_text="Instagram profile URL"
    )
    twitter_url = models.URLField(
        blank=True,
        help_text="Twitter/X profile URL"
    )
    linkedin_url = models.URLField(
        blank=True,
        help_text="LinkedIn company page URL"
    )
    
    # Status & Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Manufacturer is active and visible"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Manufacturer is verified by ProudlyZimmart"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this manufacturer prominently"
    )
    
    # SEO & Metadata
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta title"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['province', 'city']),
        ]
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Manufacturer.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for manufacturer detail page."""
        return reverse('manufacturers:manufacturer-detail', kwargs={'pk': self.pk})
    
    def get_product_count(self):
        """Get count of active products from this manufacturer."""
        return self.products.filter(is_active=True).count()
    
    # Wagtail Panels Configuration
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('short_description'),
        ], heading="Basic Information"),
        
        MultiFieldPanel([
            FieldPanel('description'),
        ], heading="Company Description"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('email'),
                FieldPanel('phone'),
            ]),
            FieldPanel('address'),
        ], heading="Contact Details"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('city'),
                FieldPanel('province'),
            ]),
            FieldPanel('country'),
        ], heading="Location"),
        
        MultiFieldPanel([
            FieldPanel('website'),
            FieldRowPanel([
                FieldPanel('facebook_url'),
                FieldPanel('instagram_url'),
            ]),
            FieldRowPanel([
                FieldPanel('twitter_url'),
                FieldPanel('linkedin_url'),
            ]),
        ], heading="Social Media & Links"),
        
        MultiFieldPanel([
            FieldPanel('logo'),
        ], heading="Logo"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('is_active'),
                FieldPanel('is_verified'),
            ]),
            FieldPanel('is_featured'),
        ], heading="Status & Settings"),
        
        MultiFieldPanel([
            FieldPanel('meta_title'),
            FieldPanel('meta_description'),
        ], heading="SEO Metadata"),
    ]
