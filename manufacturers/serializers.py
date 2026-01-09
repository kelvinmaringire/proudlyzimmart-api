"""
Serializers for the manufacturers app.
Handles serialization of manufacturer profiles and related data.
"""
from rest_framework import serializers
from .models import Manufacturer, ManufacturerSubmission


class ManufacturerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for manufacturer lists."""
    logo_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Manufacturer
        fields = (
            'id', 'name', 'slug', 'short_description',
            'logo_url', 'city', 'province', 'country',
            'website', 'is_active', 'is_verified', 'is_featured',
            'product_count', 'created_at'
        )
        read_only_fields = ('id', 'slug', 'created_at')
    
    def get_logo_url(self, obj):
        """Get full logo URL."""
        if obj.logo and obj.logo.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.file.url)
            return obj.logo.file.url
        return None
    
    def get_product_count(self, obj):
        """Get count of active products from this manufacturer."""
        return obj.get_product_count()


class ManufacturerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for manufacturer detail view."""
    logo_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    
    class Meta:
        model = Manufacturer
        fields = (
            'id', 'name', 'slug', 'short_description', 'description',
            'logo_url', 'email', 'phone', 'address',
            'city', 'province', 'country',
            'website', 'facebook_url', 'instagram_url',
            'twitter_url', 'linkedin_url', 'social_links',
            'is_active', 'is_verified', 'is_featured',
            'meta_title', 'meta_description',
            'product_count', 'products',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')
    
    def get_logo_url(self, obj):
        """Get full logo URL."""
        if obj.logo and obj.logo.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.file.url)
            return obj.logo.file.url
        return None
    
    def get_product_count(self, obj):
        """Get count of active products from this manufacturer."""
        return obj.get_product_count()
    
    def get_products(self, obj):
        """Get basic information about manufacturer's products."""
        products = obj.products.filter(is_active=True)[:10]  # Limit to 10
        return [
            {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'sku': product.sku,
                'price_usd': float(product.price_usd) if product.price_usd else None,
                'price_zwl': float(product.price_zwl) if product.price_zwl else None,
                'price_zar': float(product.price_zar) if product.price_zar else None,
                'primary_image': self._get_primary_image(product),
            }
            for product in products
        ]
    
    def _get_primary_image(self, product):
        """Get primary image URL for a product."""
        primary_image = product.images.filter(is_primary=True).first()
        if primary_image and primary_image.image and primary_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.file.url)
            return primary_image.image.file.url
        
        # Fallback to first image
        first_image = product.images.first()
        if first_image and first_image.image and first_image.image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.file.url)
            return first_image.image.file.url
        return None
    
    def get_social_links(self, obj):
        """Get social media links as a dictionary."""
        return {
            'website': obj.website,
            'facebook': obj.facebook_url,
            'instagram': obj.instagram_url,
            'twitter': obj.twitter_url,
            'linkedin': obj.linkedin_url,
        }


class ManufacturerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating manufacturers."""
    logo_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Manufacturer
        fields = (
            'name', 'short_description', 'description',
            'logo_id', 'email', 'phone', 'address',
            'city', 'province', 'country',
            'website', 'facebook_url', 'instagram_url',
            'twitter_url', 'linkedin_url',
            'is_active', 'is_verified', 'is_featured',
            'meta_title', 'meta_description'
        )
    
    def validate(self, data):
        """Validate manufacturer data."""
        # Ensure at least name and description are provided
        if not data.get('name'):
            raise serializers.ValidationError("Name is required.")
        if not data.get('description'):
            raise serializers.ValidationError("Description is required.")
        return data
    
    def create(self, validated_data):
        """Create manufacturer with logo."""
        logo_id = validated_data.pop('logo_id', None)
        
        if logo_id:
            from wagtail.images.models import Image
            try:
                logo = Image.objects.get(id=logo_id)
                validated_data['logo'] = logo
            except Image.DoesNotExist:
                raise serializers.ValidationError({"logo_id": "Image not found."})
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update manufacturer with logo."""
        logo_id = validated_data.pop('logo_id', None)
        
        if logo_id is not None:
            if logo_id:
                from wagtail.images.models import Image
                try:
                    logo = Image.objects.get(id=logo_id)
                    validated_data['logo'] = logo
                except Image.DoesNotExist:
                    raise serializers.ValidationError({"logo_id": "Image not found."})
            else:
                validated_data['logo'] = None
        
        return super().update(instance, validated_data)


class ManufacturerSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating manufacturer submissions (public endpoint)."""
    
    class Meta:
        model = ManufacturerSubmission
        fields = (
            'name', 'email', 'phone',
            'company_name', 'description', 'website',
            'city', 'province', 'country',
            'product_types', 'product_categories'
        )
    
    def validate(self, data):
        """Validate submission data."""
        # Ensure required fields are present
        if not data.get('name'):
            raise serializers.ValidationError("Name is required.")
        if not data.get('email'):
            raise serializers.ValidationError("Email is required.")
        if not data.get('phone'):
            raise serializers.ValidationError("Phone number is required.")
        return data


class ManufacturerSubmissionAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin viewing/updating manufacturer submissions."""
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = ManufacturerSubmission
        fields = (
            'id', 'name', 'email', 'phone',
            'company_name', 'description', 'website',
            'city', 'province', 'country',
            'product_types', 'product_categories',
            'status', 'admin_notes', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def update(self, instance, validated_data):
        """Update submission and set reviewed_by/reviewed_at if status changes."""
        # If status is being changed from pending, set reviewed_by and reviewed_at
        if 'status' in validated_data:
            new_status = validated_data['status']
            if instance.status == 'pending' and new_status != 'pending':
                if not validated_data.get('reviewed_by'):
                    validated_data['reviewed_by'] = self.context['request'].user
                if not validated_data.get('reviewed_at'):
                    from django.utils import timezone
                    validated_data['reviewed_at'] = timezone.now()
        
        return super().update(instance, validated_data)

