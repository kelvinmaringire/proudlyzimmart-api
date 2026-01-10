"""
Serializers for the blog app.
Handles serialization of blog posts and related data.
"""
from rest_framework import serializers
from rest_framework.fields import CharField
from wagtail.rich_text import expand_db_html
from .models import BlogPost


class RichTextSerializer(CharField):
    """Serializer for Wagtail RichTextField that expands database HTML to display HTML."""
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation:
            return expand_db_html(representation)
        return representation


class BlogPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for blog post lists."""
    featured_image_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'excerpt',
            'featured_image_url', 'author_name',
            'published_date', 'is_published',
            'view_count', 'created_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'view_count')
    
    def get_featured_image_url(self, obj):
        """Get full featured image URL."""
        if obj.featured_image and obj.featured_image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.file.url)
            return obj.featured_image.file.url
        return None
    
    def get_author_name(self, obj):
        """Get author's full name or username."""
        if obj.author:
            if obj.author.get_full_name():
                return obj.author.get_full_name()
            return obj.author.username
        return None


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for blog post detail view."""
    featured_image_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    author_username = serializers.SerializerMethodField()
    content = RichTextSerializer()
    
    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'excerpt', 'content',
            'featured_image_url', 'author', 'author_name', 'author_username',
            'published_date', 'is_published',
            'view_count',
            'meta_title', 'meta_description',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at', 'view_count')
    
    def get_featured_image_url(self, obj):
        """Get full featured image URL."""
        if obj.featured_image and obj.featured_image.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.file.url)
            return obj.featured_image.file.url
        return None
    
    def get_author_name(self, obj):
        """Get author's full name or username."""
        if obj.author:
            if obj.author.get_full_name():
                return obj.author.get_full_name()
            return obj.author.username
        return None
    
    def get_author_username(self, obj):
        """Get author's username."""
        if obj.author:
            return obj.author.username
        return None


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating blog posts."""
    featured_image_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = BlogPost
        fields = (
            'title', 'excerpt', 'content',
            'featured_image_id', 'author',
            'published_date', 'is_published',
            'meta_title', 'meta_description'
        )
    
    def validate(self, data):
        """Validate blog post data."""
        # Ensure at least title and content are provided
        if not data.get('title'):
            raise serializers.ValidationError("Title is required.")
        if not data.get('content'):
            raise serializers.ValidationError("Content is required.")
        return data
    
    def create(self, validated_data):
        """Create blog post with featured image."""
        featured_image_id = validated_data.pop('featured_image_id', None)
        
        if featured_image_id:
            from wagtail.images.models import Image
            try:
                featured_image = Image.objects.get(id=featured_image_id)
                validated_data['featured_image'] = featured_image
            except Image.DoesNotExist:
                raise serializers.ValidationError({"featured_image_id": "Image not found."})
        
        # Set author to current user if not provided
        if 'author' not in validated_data or not validated_data.get('author'):
            validated_data['author'] = self.context['request'].user
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update blog post with featured image."""
        featured_image_id = validated_data.pop('featured_image_id', None)
        
        if featured_image_id is not None:
            if featured_image_id:
                from wagtail.images.models import Image
                try:
                    featured_image = Image.objects.get(id=featured_image_id)
                    validated_data['featured_image'] = featured_image
                except Image.DoesNotExist:
                    raise serializers.ValidationError({"featured_image_id": "Image not found."})
            else:
                validated_data['featured_image'] = None
        
        return super().update(instance, validated_data)

