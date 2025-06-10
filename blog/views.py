from django.shortcuts import render, get_object_or_404
from .models import BlogPost
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer
from rest_framework import generics, permissions

class PublicBlogPostListView(generics.ListAPIView):
    queryset = BlogPost.objects.filter(status='published').order_by('-published_at')
    serializer_class = BlogPostListSerializer
    permission_classes = [permissions.AllowAny]

class PublicBlogPostDetailView(generics.RetrieveAPIView):
    queryset = BlogPost.objects.filter(status='published')
    serializer_class = BlogPostDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]

def post_list(request):
    """View for listing all blog posts"""
    posts = BlogPost.objects.filter(status='published').order_by('-published_at')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, slug):
    """View for displaying a single blog post"""
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    post.increment_view_count()
    return render(request, 'blog/post_detail.html', {'post': post})
