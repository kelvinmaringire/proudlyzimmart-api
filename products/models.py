"""
Product models for ProudlyZimmart marketplace.
Handles products, categories, variations, images, reviews, and related products.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
)
from wagtail.images.models import Image

User = get_user_model()


class Category(models.Model):
    """Product category with support for hierarchical subcategories."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for subcategories"
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category-detail', kwargs={'slug': self.slug})


class ProductType(models.Model):
    """Product type: Ready to Buy, Collect, Enquire, Promotional."""
    TYPE_CHOICES = [
        ('ready_to_buy', 'Ready to Buy'),
        ('collect', 'Collect'),
        ('enquire', 'Enquire'),
        ('promotional', 'Promotional'),
    ]
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['type']

    def __str__(self):
        return self.name


class Product(ClusterableModel):
    """Main product model for ProudlyZimmart marketplace."""
    # Basic Information
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name='products'
    )
    
    # Branding (must be Zimbabwean)
    brand = models.CharField(max_length=200, help_text="Brand name (must be Zimbabwean)")
    manufacturer = models.ForeignKey(
        'manufacturers.Manufacturer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Manufacturer/Company supplying this product"
    )
    is_proudlyzimmart_brand = models.BooleanField(
        default=False,
        help_text="Product is ProudlyZimmart's own brand"
    )
    
    # Pricing (multi-currency support: USD, ZWL RTGS, ZAR)
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Price in USD"
    )
    price_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Price in ZWL RTGS"
    )
    price_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Price in ZAR"
    )
    sale_price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Sale price in USD"
    )
    sale_price_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Sale price in ZWL RTGS"
    )
    sale_price_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Sale price in ZAR"
    )
    
    # Stock Management
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Available stock quantity"
    )
    low_stock_threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Alert when stock falls below this"
    )
    track_stock = models.BooleanField(
        default=True,
        help_text="Track stock for this product"
    )
    in_stock = models.BooleanField(default=True)
    
    # Product Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_standard = models.BooleanField(
        default=True,
        help_text="Product meets standard requirements"
    )
    
    # Metadata
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg"
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="Dimensions (L x W x H)"
    )
    
    # SEO & Display
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags"
    )
    
    # Ratings & Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-generate SKU if not provided
        if not self.sku:
            base_sku = slugify(self.name).upper()[:10]
            sku = base_sku
            counter = 1
            while Product.objects.filter(sku=sku).exists():
                sku = f"{base_sku}{counter:04d}"
                counter += 1
            self.sku = sku
        
        # Update in_stock based on stock_quantity
        if self.track_stock:
            self.in_stock = self.stock_quantity > 0
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.slug})

    def get_current_price(self, currency='USD'):
        """Get current price (sale price if available, otherwise regular price)."""
        if currency.upper() == 'USD':
            return self.sale_price_usd if self.sale_price_usd else self.price_usd
        elif currency.upper() == 'ZWL':
            return self.sale_price_zwl if self.sale_price_zwl else self.price_zwl
        elif currency.upper() == 'ZAR':
            return self.sale_price_zar if self.sale_price_zar else self.price_zar
        return self.price_usd

    def is_on_sale(self):
        """Check if product is on sale."""
        return bool(
            (self.sale_price_usd and self.sale_price_usd < self.price_usd) or
            (self.sale_price_zwl and self.sale_price_zwl < self.price_zwl) or
            (self.sale_price_zar and self.sale_price_zar < self.price_zar)
        )

    def update_rating(self):
        """Update average rating and review count."""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            self.average_rating = reviews.aggregate(
                avg=models.Avg('rating')
            )['avg'] or 0.00
            self.review_count = reviews.count()
        else:
            self.average_rating = 0.00
            self.review_count = 0
        self.save(update_fields=['average_rating', 'review_count'])

    # Wagtail Panels Configuration
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldRowPanel([
                FieldPanel('sku'),
                FieldPanel('category'),
            ]),
        ], heading="Basic Information"),
        
        MultiFieldPanel([
            FieldPanel('short_description'),
            FieldPanel('description'),
        ], heading="Description"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('brand'),
                FieldPanel('manufacturer'),
            ]),
            FieldPanel('product_type'),
            FieldPanel('is_proudlyzimmart_brand'),
        ], heading="Branding & Categorization"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('price_usd'),
                FieldPanel('sale_price_usd'),
            ]),
            FieldRowPanel([
                FieldPanel('price_zwl'),
                FieldPanel('sale_price_zwl'),
            ]),
            FieldRowPanel([
                FieldPanel('price_zar'),
                FieldPanel('sale_price_zar'),
            ]),
        ], heading="Pricing"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('stock_quantity'),
                FieldPanel('low_stock_threshold'),
            ]),
            FieldRowPanel([
                FieldPanel('track_stock'),
                FieldPanel('in_stock'),
            ]),
        ], heading="Stock Management"),
        
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('weight'),
                FieldPanel('dimensions'),
            ]),
        ], heading="Physical Attributes"),
        
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('is_featured'),
            FieldPanel('is_standard'),
        ], heading="Product Status"),
        
        MultiFieldPanel([
            FieldPanel('meta_title'),
            FieldPanel('meta_description'),
            FieldPanel('tags'),
        ], heading="SEO & Metadata"),
        
        MultiFieldPanel([
            InlinePanel('images', label=""),
        ], heading="Product Images"),
        
        MultiFieldPanel([
            InlinePanel('videos', label=""),
        ], heading="Product Videos"),
    ]


class ProductVariation(models.Model):
    """Product variations (sizes, colors, models, etc.)."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variations'
    )
    name = models.CharField(
        max_length=100,
        help_text="Variation name (e.g., 'Size', 'Color', 'Model')"
    )
    value = models.CharField(
        max_length=100,
        help_text="Variation value (e.g., 'Large', 'Red', 'Model X')"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="SKU for this variation"
    )
    price_adjustment_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price adjustment in USD (+/-)"
    )
    price_adjustment_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price adjustment in ZWL RTGS (+/-)"
    )
    price_adjustment_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price adjustment in ZAR (+/-)"
    )
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name', 'value']
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

    def save(self, *args, **kwargs):
        if not self.sku:
            base_sku = f"{self.product.sku}-{slugify(self.name)}-{slugify(self.value)}"
            self.sku = base_sku.upper()[:50]
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Multiple images per product with zoom support."""
    product = ParentalKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='product_images',
        help_text="Select an image from the Wagtail image library"
    )
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary product image"
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_primary', 'order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    panels = [
        FieldPanel('image'),
        FieldRowPanel([
            FieldPanel('alt_text'),
            FieldPanel('is_primary'),
        ]),
        FieldPanel('order'),
    ]


class Review(models.Model):
    """Customer reviews and ratings for products."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(
        default=False,
        help_text="Review approved by admin"
    )
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="Reviewer purchased this product"
    )
    helpful_count = models.IntegerField(
        default=0,
        help_text="Number of users who found this helpful"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} stars"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating when review is saved
        if self.is_approved:
            self.product.update_rating()


class RelatedProduct(models.Model):
    """Related products / recommendations."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_products'
    )
    related_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_to_products'
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['product', 'related_product']

    def __str__(self):
        return f"{self.product.name} -> {self.related_product.name}"


class ProductVideo(models.Model):
    """Product videos for showcasing products (primarily YouTube URLs)."""
    product = ParentalKey(
        Product,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video_url = models.URLField(
        help_text="YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
    )
    thumbnail = models.ImageField(
        upload_to='product_videos/thumbnails/',
        blank=True,
        null=True,
        help_text="Video thumbnail image (optional, will use YouTube thumbnail if not provided)"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Video title (optional, can be extracted from YouTube)"
    )
    description = models.TextField(
        blank=True,
        help_text="Video description"
    )
    video_type = models.CharField(
        max_length=20,
        choices=[
            ('youtube', 'YouTube'),
            ('vimeo', 'Vimeo'),
            ('direct', 'Direct Link'),
            ('other', 'Other'),
        ],
        default='youtube',
        help_text="Type of video platform"
    )
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Video duration in seconds"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary product video"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_primary', 'order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Video {self.order}"

    def save(self, *args, **kwargs):
        # Auto-detect video type from URL
        if self.video_url:
            if 'youtube.com' in self.video_url or 'youtu.be' in self.video_url:
                self.video_type = 'youtube'
            elif 'vimeo.com' in self.video_url:
                self.video_type = 'vimeo'
            else:
                self.video_type = 'direct'
        
        # Ensure only one primary video per product
        if self.is_primary:
            ProductVideo.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def get_youtube_video_id(self):
        """Extract YouTube video ID from URL."""
        if self.video_type != 'youtube':
            return None
        
        import re
        # Handle different YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.video_url)
            if match:
                return match.group(1)
        return None

    def get_youtube_embed_url(self):
        """Get YouTube embed URL for iframe."""
        video_id = self.get_youtube_video_id()
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return None

    def get_youtube_thumbnail_url(self):
        """Get YouTube thumbnail URL (if thumbnail not uploaded)."""
        video_id = self.get_youtube_video_id()
        if video_id:
            # YouTube provides different quality thumbnails
            # hqdefault = 480x360, maxresdefault = 1280x720 (if available)
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        return None

    panels = [
        FieldPanel('video_url'),
        FieldRowPanel([
            FieldPanel('video_type'),
            FieldPanel('is_primary'),
        ]),
        FieldPanel('thumbnail'),
        FieldPanel('title'),
        FieldPanel('description'),
        FieldRowPanel([
            FieldPanel('duration'),
            FieldPanel('is_active'),
        ]),
        FieldPanel('order'),
    ]


class ProductBundle(models.Model):
    """Product bundles/packages combining multiple products at a discount."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    
    # Bundle Pricing (multi-currency)
    bundle_price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Bundle price in USD"
    )
    bundle_price_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Bundle price in ZWL RTGS"
    )
    bundle_price_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Bundle price in ZAR"
    )
    
    # Discount Information
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)"
    )
    savings_amount_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount saved in USD"
    )
    savings_amount_zwl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount saved in ZWL RTGS"
    )
    savings_amount_zar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount saved in ZAR"
    )
    
    # Bundle Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Display
    image = models.ImageField(
        upload_to='bundles/',
        blank=True,
        null=True,
        help_text="Bundle image"
    )
    
    # Metadata
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while ProductBundle.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Calculate savings if bundle price is set
        if self.bundle_price_usd or self.bundle_price_zwl or self.bundle_price_zar:
            self._calculate_savings()
        
        super().save(*args, **kwargs)

    def _calculate_savings(self):
        """Calculate savings amount based on individual product prices."""
        items = self.bundle_items.select_related('product').all()
        
        total_usd = 0
        total_zwl = 0
        total_zar = 0
        
        for item in items:
            product = item.product
            quantity = item.quantity
            
            if product.price_usd:
                total_usd += float(product.price_usd) * quantity
            if product.price_zwl:
                total_zwl += float(product.price_zwl) * quantity
            if product.price_zar:
                total_zar += float(product.price_zar) * quantity
        
        # Calculate savings
        if self.bundle_price_usd and total_usd > 0:
            self.savings_amount_usd = total_usd - float(self.bundle_price_usd)
            if total_usd > 0:
                self.discount_percentage = ((self.savings_amount_usd / total_usd) * 100)
        
        if self.bundle_price_zwl and total_zwl > 0:
            self.savings_amount_zwl = total_zwl - float(self.bundle_price_zwl)
        
        if self.bundle_price_zar and total_zar > 0:
            self.savings_amount_zar = total_zar - float(self.bundle_price_zar)

    def get_absolute_url(self):
        return reverse('products:bundle-detail', kwargs={'slug': self.slug})

    def get_total_individual_price(self, currency='USD'):
        """Get total price if products were bought individually."""
        items = self.bundle_items.select_related('product').all()
        total = 0
        
        for item in items:
            product = item.product
            quantity = item.quantity
            
            if currency.upper() == 'USD' and product.price_usd:
                total += float(product.price_usd) * quantity
            elif currency.upper() == 'ZWL' and product.price_zwl:
                total += float(product.price_zwl) * quantity
            elif currency.upper() == 'ZAR' and product.price_zar:
                total += float(product.price_zar) * quantity
        
        return total

    def get_bundle_price(self, currency='USD'):
        """Get bundle price for specified currency."""
        if currency.upper() == 'USD':
            return self.bundle_price_usd
        elif currency.upper() == 'ZWL':
            return self.bundle_price_zwl
        elif currency.upper() == 'ZAR':
            return self.bundle_price_zar
        return self.bundle_price_usd


class BundleItem(models.Model):
    """Items included in a product bundle."""
    bundle = models.ForeignKey(
        ProductBundle,
        on_delete=models.CASCADE,
        related_name='bundle_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='bundles'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity of this product in the bundle"
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['bundle', 'product']

    def __str__(self):
        return f"{self.bundle.name} - {self.product.name} (x{self.quantity})"
