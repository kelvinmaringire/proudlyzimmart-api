"""
Blog models for ProudlyZimmart.
Handles blog posts for telling stories about Zimbabwean products and manufacturers.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, FieldRowPanel
)
from wagtail.fields import RichTextField
from wagtail.images.models import Image

User = get_user_model()


class BlogPost(models.Model):
    """Blog post model for publishing stories about Zimbabwean products and community."""
    
    # Basic Information
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short excerpt/summary for listings"
    )
    content = RichTextField(
        help_text="Full blog post content"
    )
    
    # Featured Image
    featured_image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Featured image for the blog post"
    )
    
    # Author
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts',
        help_text="Author of the blog post"
    )
    
    # Publishing
    published_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when the post was published"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether the post is published and visible"
    )
    
    # View Tracking
    view_count = models.IntegerField(
        default=0,
        help_text="Number of times this post has been viewed"
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
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', 'published_date']),
            models.Index(fields=['author', 'is_published']),
        ]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set published_date when is_published is set to True for the first time
        if self.is_published and not self.published_date:
            from django.utils import timezone
            self.published_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for blog post detail page."""
        return reverse('blog:blogpost-detail', kwargs={'pk': self.pk})
    
    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    # Wagtail Panels Configuration
    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('slug'),
            FieldPanel('excerpt'),
        ], heading="Basic Information"),
        
        MultiFieldPanel([
            FieldPanel('content'),
        ], heading="Content"),
        
        MultiFieldPanel([
            FieldPanel('featured_image'),
        ], heading="Featured Image"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('author'),
                FieldPanel('is_published'),
            ]),
            FieldPanel('published_date'),
        ], heading="Publishing"),
        
        MultiFieldPanel([
            FieldPanel('view_count'),
        ], heading="Statistics"),
        
        MultiFieldPanel([
            FieldPanel('meta_title'),
            FieldPanel('meta_description'),
        ], heading="SEO Metadata"),
    ]
