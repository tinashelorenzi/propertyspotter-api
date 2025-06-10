from rest_framework import serializers
from .models import BlogPost

class BlogPostListSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'excerpt', 'featured_image_url', 'status', 'published_at']
    def get_featured_image_url(self, obj):
        request = self.context.get('request')
        if obj.featured_image and hasattr(obj.featured_image, 'url'):
            url = obj.featured_image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class BlogPostDetailSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'featured_image_url', 'status', 'published_at']
    def get_featured_image_url(self, obj):
        request = self.context.get('request')
        if obj.featured_image and hasattr(obj.featured_image, 'url'):
            url = obj.featured_image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None 