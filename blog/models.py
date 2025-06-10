# blog/models.py

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from meta.models import ModelMeta


def blog_image_upload_path(instance, filename):
    """Generate upload path for blog post featured images"""
    return f'blog/featured_images/{instance.slug}/{filename}'


class BlogCategory(models.Model):
    """Categories for blog posts"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(ModelMeta, models.Model):
    """Main blog post model with SEO capabilities"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.TextField(
        max_length=300, 
        help_text="Brief description of the post (max 300 characters)"
    )
    content = RichTextUploadingField(
        help_text="Main content of the blog post with rich text editor"
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to=blog_image_upload_path,
        blank=True,
        null=True,
        help_text="Main image for the blog post"
    )
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alt text for the featured image (SEO)"
    )
    
    # Classification
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    tags = TaggableManager(blank=True, help_text="Add tags separated by commas")
    
    # Publishing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this post prominently on the blog homepage"
    )
    
    # SEO fields
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="SEO title (max 60 characters). If empty, uses post title."
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (max 160 characters). If empty, uses excerpt."
    )
    
    # Relationships
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None
        
        # Auto-generate meta fields if empty
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = self.excerpt[:160]
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def increment_view_count(self):
        """Increment the view count for this post"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        import re
        from django.utils.html import strip_tags
        
        # Strip HTML tags and count words
        text = strip_tags(self.content)
        word_count = len(re.findall(r'\w+', text))
        
        # Average reading speed is 200-250 words per minute
        minutes = max(1, round(word_count / 225))
        return minutes
    
    # SEO Meta configuration
    _metadata = {
        'title': 'meta_title',
        'description': 'meta_description',
        'image': 'get_meta_image',
        'url': 'get_absolute_url',
        'object_type': 'article',
        'site_name': 'PropertySpotter Blog',
        'twitter_site': '@PropertySpotter',
        'twitter_creator': '@PropertySpotter',
        'fb_app_id': '',  # Add your Facebook App ID if you have one
    }
    
    def get_meta_image(self):
        if self.featured_image:
            return self.featured_image.url
        return None


class BlogComment(models.Model):
    """Comments on blog posts"""
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.author_name} on {self.post.title}'


class BlogNewsletterSubscriber(models.Model):
    """Newsletter subscribers from the blog"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.email