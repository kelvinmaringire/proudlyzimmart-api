"""
Serializers for the products app.
Handles serialization of products, categories, variations, images, reviews, and related products.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category,
    ProductType,
    Product,
    ProductVariation,
    ProductImage,
    Review,
    RelatedProduct,
    ProductVideo,
    ProductBundle,
    BundleItem,
)

User = get_user_model()


class ManufacturerSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Manufacturer in product serializers."""
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Will be set dynamically
        fields = (
            'id', 'name', 'slug', 'short_description',
            'logo_url', 'city', 'province', 'country',
            'website', 'is_verified', 'is_featured'
        )
    
    def __init__(self, *args, **kwargs):
        # Import here to avoid circular imports
        from manufacturers.models import Manufacturer
        self.Meta.model = Manufacturer
        super().__init__(*args, **kwargs)
    
    def get_logo_url(self, obj):
        """Get full logo URL."""
        if obj and obj.logo and obj.logo.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.file.url)
            return obj.logo.file.url
        return None


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'parent', 'image',
            'is_active', 'order', 'children', 'product_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_children(self, obj):
        """Get child categories."""
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data

    def get_product_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductTypeSerializer(serializers.ModelSerializer):
    """Serializer for ProductType model."""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductType
        fields = ('id', 'type', 'name', 'description', 'is_active', 'product_count')
        read_only_fields = ('id',)

    def get_product_count(self, obj):
        """Get count of active products of this type."""
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = (
            'id', 'image', 'image_url', 'alt_text', 'is_primary',
            'order', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_image_url(self, obj):
        """Get full image URL."""
        if obj.image and obj.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.file.url)
            return obj.image.file.url
        return None


class ProductVariationSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariation model."""

    class Meta:
        model = ProductVariation
        fields = (
            'id', 'name', 'value', 'sku', 'price_adjustment_usd',
            'price_adjustment_zwl', 'price_adjustment_zar',
            'stock_quantity', 'is_active', 'order'
        )
        read_only_fields = ('id', 'sku')


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    user = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'product', 'user', 'user_name', 'rating', 'title',
            'comment', 'is_approved', 'is_verified_purchase',
            'helpful_count', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'is_approved', 'helpful_count',
            'created_at', 'updated_at'
        )

    def get_user(self, obj):
        """Get user information."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

    def create(self, validated_data):
        """Create review and set user from request."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RelatedProductSerializer(serializers.ModelSerializer):
    """Serializer for RelatedProduct model."""
    related_product_detail = serializers.SerializerMethodField()

    class Meta:
        model = RelatedProduct
        fields = ('id', 'product', 'related_product', 'related_product_detail', 'order')
        read_only_fields = ('id',)

    def get_related_product_detail(self, obj):
        """Get basic product information."""
        return {
            'id': obj.related_product.id,
            'name': obj.related_product.name,
            'slug': obj.related_product.slug,
            'sku': obj.related_product.sku,
            'price_usd': obj.related_product.price_usd,
            'average_rating': obj.related_product.average_rating,
            'primary_image': self._get_primary_image(obj.related_product),
        }

    def _get_primary_image(self, product):
        """Get primary image URL."""
        primary_image = product.images.filter(is_primary=True).first()
        if primary_image and primary_image.image and primary_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.file.url)
            return primary_image.image.file.url
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists."""
    category = CategorySerializer(read_only=True)
    product_type = ProductTypeSerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    current_price_usd = serializers.SerializerMethodField()
    current_price_zwl = serializers.SerializerMethodField()
    current_price_zar = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'short_description',
            'category', 'product_type', 'brand', 'manufacturer', 'is_proudlyzimmart_brand',
            'price_usd', 'price_zwl', 'price_zar',
            'sale_price_usd', 'sale_price_zwl', 'sale_price_zar',
            'current_price_usd', 'current_price_zwl', 'current_price_zar',
            'is_on_sale', 'discount_percentage',
            'stock_quantity', 'in_stock', 'is_active', 'is_featured',
            'average_rating', 'review_count', 'primary_image',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'slug', 'sku', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        )

    def get_primary_image(self, obj):
        """Get primary image URL."""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image and primary_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.file.url)
            return primary_image.image.file.url
        
        # Fallback to first image if no primary
        first_image = obj.images.first()
        if first_image and first_image.image and first_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.file.url)
            return first_image.image.file.url
        return None

    def get_current_price_usd(self, obj):
        """Get current USD price."""
        return float(obj.get_current_price('USD')) if obj.get_current_price('USD') else None

    def get_current_price_zwl(self, obj):
        """Get current ZWL price."""
        return float(obj.get_current_price('ZWL')) if obj.get_current_price('ZWL') else None

    def get_current_price_zar(self, obj):
        """Get current ZAR price."""
        return float(obj.get_current_price('ZAR')) if obj.get_current_price('ZAR') else None

    def get_is_on_sale(self, obj):
        """Check if product is on sale."""
        return obj.is_on_sale()

    def get_discount_percentage(self, obj):
        """Calculate discount percentage."""
        if obj.is_on_sale():
            if obj.price_usd and obj.sale_price_usd:
                discount = ((obj.price_usd - obj.sale_price_usd) / obj.price_usd) * 100
                return round(discount, 2)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for product detail view."""
    category = CategorySerializer(read_only=True)
    product_type = ProductTypeSerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    videos = serializers.SerializerMethodField()
    variations = ProductVariationSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    current_price_usd = serializers.SerializerMethodField()
    current_price_zwl = serializers.SerializerMethodField()
    current_price_zar = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'description', 'short_description',
            'category', 'product_type', 'brand', 'manufacturer',
            'is_proudlyzimmart_brand',
            'price_usd', 'price_zwl', 'price_zar',
            'sale_price_usd', 'sale_price_zwl', 'sale_price_zar',
            'current_price_usd', 'current_price_zwl', 'current_price_zar',
            'is_on_sale', 'discount_percentage',
            'stock_quantity', 'low_stock_threshold', 'track_stock',
            'in_stock', 'is_active', 'is_featured', 'is_standard',
            'weight', 'dimensions', 'meta_title', 'meta_description',
            'tags', 'average_rating', 'review_count',
            'images', 'videos', 'variations', 'reviews', 'related_products',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'slug', 'sku', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        )

    def get_videos(self, obj):
        """Get product videos."""
        videos = obj.videos.filter(is_active=True)
        return ProductVideoSerializer(videos, many=True, context=self.context).data

    def get_reviews(self, obj):
        """Get approved reviews."""
        reviews = obj.reviews.filter(is_approved=True)[:10]  # Limit to 10 most recent
        return ReviewSerializer(reviews, many=True, context=self.context).data

    def get_related_products(self, obj):
        """Get related products."""
        related = obj.related_products.select_related('related_product')[:10]
        return RelatedProductSerializer(related, many=True, context=self.context).data

    def get_current_price_usd(self, obj):
        """Get current USD price."""
        return float(obj.get_current_price('USD')) if obj.get_current_price('USD') else None

    def get_current_price_zwl(self, obj):
        """Get current ZWL price."""
        return float(obj.get_current_price('ZWL')) if obj.get_current_price('ZWL') else None

    def get_current_price_zar(self, obj):
        """Get current ZAR price."""
        return float(obj.get_current_price('ZAR')) if obj.get_current_price('ZAR') else None

    def get_is_on_sale(self, obj):
        """Check if product is on sale."""
        return obj.is_on_sale()

    def get_discount_percentage(self, obj):
        """Calculate discount percentage."""
        if obj.is_on_sale():
            if obj.price_usd and obj.sale_price_usd:
                discount = ((obj.price_usd - obj.sale_price_usd) / obj.price_usd) * 100
                return round(discount, 2)
        return None


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    product_type_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Product
        fields = (
            'name', 'description', 'short_description', 'category_id',
            'product_type_id', 'brand', 'manufacturer', 'is_proudlyzimmart_brand',
            'price_usd', 'price_zwl', 'price_zar',
            'sale_price_usd', 'sale_price_zwl', 'sale_price_zar',
            'stock_quantity', 'low_stock_threshold', 'track_stock',
            'is_active', 'is_featured', 'is_standard',
            'weight', 'dimensions', 'meta_title', 'meta_description', 'tags'
        )

    def validate(self, data):
        """Validate product data."""
        # Ensure at least one price is set
        prices = [
            data.get('price_usd'), data.get('price_zwl'), data.get('price_zar')
        ]
        if not any(prices):
            raise serializers.ValidationError(
                "At least one price (USD, ZWL, or ZAR) must be set."
            )
        
        # Validate sale prices are less than regular prices
        if data.get('sale_price_usd') and data.get('price_usd'):
            if data['sale_price_usd'] >= data['price_usd']:
                raise serializers.ValidationError(
                    "Sale price must be less than regular price."
                )
        
        if data.get('sale_price_zwl') and data.get('price_zwl'):
            if data['sale_price_zwl'] >= data['price_zwl']:
                raise serializers.ValidationError(
                    "Sale price must be less than regular price."
                )
        
        if data.get('sale_price_zar') and data.get('price_zar'):
            if data['sale_price_zar'] >= data['price_zar']:
                raise serializers.ValidationError(
                    "Sale price must be less than regular price."
                )
        
        return data

    def create(self, validated_data):
        """Create product with category, product_type, and manufacturer."""
        category_id = validated_data.pop('category_id', None)
        product_type_id = validated_data.pop('product_type_id')
        manufacturer_id = validated_data.pop('manufacturer_id', None)
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category_id": "Category not found."})
        
        try:
            product_type = ProductType.objects.get(id=product_type_id)
            validated_data['product_type'] = product_type
        except ProductType.DoesNotExist:
            raise serializers.ValidationError({"product_type_id": "Product type not found."})
        
        if manufacturer_id:
            from manufacturers.models import Manufacturer
            try:
                manufacturer = Manufacturer.objects.get(id=manufacturer_id)
                validated_data['manufacturer'] = manufacturer
            except Manufacturer.DoesNotExist:
                raise serializers.ValidationError({"manufacturer_id": "Manufacturer not found."})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update product with category, product_type, and manufacturer."""
        category_id = validated_data.pop('category_id', None)
        product_type_id = validated_data.pop('product_type_id', None)
        manufacturer_id = validated_data.pop('manufacturer_id', None)
        
        if category_id is not None:
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    validated_data['category'] = category
                except Category.DoesNotExist:
                    raise serializers.ValidationError({"category_id": "Category not found."})
            else:
                validated_data['category'] = None
        
        if product_type_id:
            try:
                product_type = ProductType.objects.get(id=product_type_id)
                validated_data['product_type'] = product_type
            except ProductType.DoesNotExist:
                raise serializers.ValidationError({"product_type_id": "Product type not found."})
        
        if manufacturer_id is not None:
            from manufacturers.models import Manufacturer
            if manufacturer_id:
                try:
                    manufacturer = Manufacturer.objects.get(id=manufacturer_id)
                    validated_data['manufacturer'] = manufacturer
                except Manufacturer.DoesNotExist:
                    raise serializers.ValidationError({"manufacturer_id": "Manufacturer not found."})
            else:
                validated_data['manufacturer'] = None
        
        return super().update(instance, validated_data)


class ProductVideoSerializer(serializers.ModelSerializer):
    """Serializer for ProductVideo model."""
    thumbnail_url = serializers.SerializerMethodField()
    youtube_video_id = serializers.SerializerMethodField()
    youtube_embed_url = serializers.SerializerMethodField()
    youtube_thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVideo
        fields = (
            'id', 'product', 'video_url', 'thumbnail', 'thumbnail_url',
            'youtube_video_id', 'youtube_embed_url', 'youtube_thumbnail_url',
            'title', 'description', 'video_type', 'duration',
            'is_primary', 'order', 'is_active', 'created_at'
        )
        read_only_fields = ('id', 'youtube_video_id', 'youtube_embed_url', 'youtube_thumbnail_url', 'created_at')

    def get_thumbnail_url(self, obj):
        """Get full thumbnail URL (uploaded thumbnail)."""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def get_youtube_video_id(self, obj):
        """Get YouTube video ID from URL."""
        return obj.get_youtube_video_id()

    def get_youtube_embed_url(self, obj):
        """Get YouTube embed URL for iframe."""
        return obj.get_youtube_embed_url()

    def get_youtube_thumbnail_url(self, obj):
        """Get YouTube thumbnail URL (fallback if no thumbnail uploaded)."""
        if obj.video_type == 'youtube':
            return obj.get_youtube_thumbnail_url()
        return None


class BundleItemSerializer(serializers.ModelSerializer):
    """Serializer for BundleItem model."""
    product_detail = serializers.SerializerMethodField()

    class Meta:
        model = BundleItem
        fields = (
            'id', 'bundle', 'product', 'product_detail',
            'quantity', 'order'
        )
        read_only_fields = ('id',)

    def get_product_detail(self, obj):
        """Get basic product information."""
        return {
            'id': obj.product.id,
            'name': obj.product.name,
            'slug': obj.product.slug,
            'sku': obj.product.sku,
            'price_usd': float(obj.product.price_usd) if obj.product.price_usd else None,
            'price_zwl': float(obj.product.price_zwl) if obj.product.price_zwl else None,
            'price_zar': float(obj.product.price_zar) if obj.product.price_zar else None,
            'primary_image': self._get_primary_image(obj.product),
        }

    def _get_primary_image(self, product):
        """Get primary image URL."""
        primary_image = product.images.filter(is_primary=True).first()
        if primary_image and primary_image.image and primary_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.file.url)
            return primary_image.image.file.url
        return None


class ProductBundleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for bundle lists."""
    image_url = serializers.SerializerMethodField()
    total_individual_price_usd = serializers.SerializerMethodField()
    total_individual_price_zwl = serializers.SerializerMethodField()
    total_individual_price_zar = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductBundle
        fields = (
            'id', 'name', 'slug', 'short_description',
            'bundle_price_usd', 'bundle_price_zwl', 'bundle_price_zar',
            'total_individual_price_usd', 'total_individual_price_zwl', 'total_individual_price_zar',
            'discount_percentage', 'savings_amount_usd', 'savings_amount_zwl', 'savings_amount_zar',
            'is_active', 'is_featured', 'image_url', 'item_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_image_url(self, obj):
        """Get bundle image URL."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_total_individual_price_usd(self, obj):
        """Get total price if bought individually in USD."""
        return float(obj.get_total_individual_price('USD')) if obj.get_total_individual_price('USD') else None

    def get_total_individual_price_zwl(self, obj):
        """Get total price if bought individually in ZWL."""
        return float(obj.get_total_individual_price('ZWL')) if obj.get_total_individual_price('ZWL') else None

    def get_total_individual_price_zar(self, obj):
        """Get total price if bought individually in ZAR."""
        return float(obj.get_total_individual_price('ZAR')) if obj.get_total_individual_price('ZAR') else None

    def get_item_count(self, obj):
        """Get number of items in bundle."""
        return obj.bundle_items.count()


class ProductBundleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for bundle detail view."""
    items = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    total_individual_price_usd = serializers.SerializerMethodField()
    total_individual_price_zwl = serializers.SerializerMethodField()
    total_individual_price_zar = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductBundle
        fields = (
            'id', 'name', 'slug', 'description', 'short_description',
            'bundle_price_usd', 'bundle_price_zwl', 'bundle_price_zar',
            'total_individual_price_usd', 'total_individual_price_zwl', 'total_individual_price_zar',
            'discount_percentage', 'savings_amount_usd', 'savings_amount_zwl', 'savings_amount_zar',
            'is_active', 'is_featured', 'image', 'image_url',
            'meta_title', 'meta_description', 'items', 'item_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_items(self, obj):
        """Get bundle items."""
        items = obj.bundle_items.select_related('product').prefetch_related('product__images')
        return BundleItemSerializer(items, many=True, context=self.context).data

    def get_image_url(self, obj):
        """Get bundle image URL."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_total_individual_price_usd(self, obj):
        """Get total price if bought individually in USD."""
        return float(obj.get_total_individual_price('USD')) if obj.get_total_individual_price('USD') else None

    def get_total_individual_price_zwl(self, obj):
        """Get total price if bought individually in ZWL."""
        return float(obj.get_total_individual_price('ZWL')) if obj.get_total_individual_price('ZWL') else None

    def get_total_individual_price_zar(self, obj):
        """Get total price if bought individually in ZAR."""
        return float(obj.get_total_individual_price('ZAR')) if obj.get_total_individual_price('ZAR') else None

    def get_item_count(self, obj):
        """Get number of items in bundle."""
        return obj.bundle_items.count()


class ProductBundleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating bundles."""
    items = BundleItemSerializer(many=True, required=False)

    class Meta:
        model = ProductBundle
        fields = (
            'name', 'description', 'short_description',
            'bundle_price_usd', 'bundle_price_zwl', 'bundle_price_zar',
            'discount_percentage', 'is_active', 'is_featured',
            'image', 'meta_title', 'meta_description', 'items'
        )

    def validate(self, data):
        """Validate bundle data."""
        # Ensure at least one bundle price is set
        prices = [
            data.get('bundle_price_usd'),
            data.get('bundle_price_zwl'),
            data.get('bundle_price_zar')
        ]
        if not any(prices):
            raise serializers.ValidationError(
                "At least one bundle price (USD, ZWL, or ZAR) must be set."
            )
        return data

    def create(self, validated_data):
        """Create bundle with items."""
        items_data = validated_data.pop('items', [])
        bundle = ProductBundle.objects.create(**validated_data)
        
        for item_data in items_data:
            BundleItem.objects.create(bundle=bundle, **item_data)
        
        # Recalculate savings
        bundle._calculate_savings()
        bundle.save()
        
        return bundle

    def update(self, instance, validated_data):
        """Update bundle with items."""
        items_data = validated_data.pop('items', None)
        
        # Update bundle fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.bundle_items.all().delete()
            
            # Create new items
            for item_data in items_data:
                BundleItem.objects.create(bundle=instance, **item_data)
            
            # Recalculate savings
            instance._calculate_savings()
            instance.save()
        
        return instance

