# blog/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import BlogPost, BlogCategory, BlogComment, BlogNewsletterSubscriber


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    def post_count(self, obj):
        count = obj.posts.filter(status='published').count()
        if count > 0:
            url = reverse('admin:blog_blogpost_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} posts</a>', url, count)
        return "0 posts"
    post_count.short_description = 'Published Posts'


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    fields = ('author_name', 'author_email', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'category', 
        'author', 
        'status', 
        'is_featured',
        'view_count',
        'published_at',
        'preview_link'
    )
    list_filter = (
        'status', 
        'is_featured', 
        'category', 
        'created_at', 
        'published_at',
        'author'
    )
    search_fields = ('title', 'excerpt', 'content', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'view_count', 
        'reading_time_display',
        'word_count_display'
    )
    # Note: tags use TaggableManager, so we can't use filter_horizontal
    inlines = [BlogCommentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 
                'slug', 
                'author', 
                'category',
                'status',
                'is_featured'
            )
        }),
        ('Content', {
            'fields': (
                'excerpt', 
                'content',
                'tags'
            )
        }),
        ('Featured Image', {
            'fields': (
                'featured_image', 
                'featured_image_alt'
            ),
            'classes': ('collapse',)
        }),
        ('SEO & Meta', {
            'fields': (
                'meta_title', 
                'meta_description'
            ),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': (
                'published_at',
            ),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': (
                'view_count',
                'reading_time_display',
                'word_count_display',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New post
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def preview_link(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">Preview</a>', url)
        return "Save first"
    preview_link.short_description = 'Preview'
    
    def reading_time_display(self, obj):
        minutes = obj.reading_time
        return f"{minutes} min read"
    reading_time_display.short_description = 'Reading Time'
    
    def word_count_display(self, obj):
        import re
        from django.utils.html import strip_tags
        text = strip_tags(obj.content)
        word_count = len(re.findall(r'\w+', text))
        return f"{word_count:,} words"
    word_count_display.short_description = 'Word Count'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-superusers can only edit their own posts
        if not request.user.is_superuser:
            qs = qs.filter(author=request.user)
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author" and not request.user.is_superuser:
            kwargs["queryset"] = request.user.__class__.objects.filter(pk=request.user.pk)
            kwargs["initial"] = request.user.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['make_published', 'make_draft', 'make_featured', 'remove_featured']
    
    def make_published(self, request, queryset):
        updated = queryset.update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} posts marked as published.')
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft', published_at=None)
        self.message_user(request, f'{updated} posts marked as draft.')
    make_draft.short_description = "Mark selected posts as draft"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts marked as featured.')
    make_featured.short_description = "Mark selected posts as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} posts removed from featured.')
    remove_featured.short_description = "Remove featured status"


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = (
        'author_name', 
        'post', 
        'is_approved', 
        'created_at',
        'content_preview'
    )
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    readonly_fields = ('created_at',)
    actions = ['approve_comments', 'reject_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments rejected.')
    reject_comments.short_description = "Reject selected comments"


@admin.register(BlogNewsletterSubscriber)
class BlogNewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at', 'unsubscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at', 'unsubscribed_at')
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{updated} subscribers activated.')
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscribers deactivated.')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


# Customize the admin site header
admin.site.site_header = "PropertySpotter Admin"
admin.site.site_title = "PropertySpotter Admin Portal"
admin.site.index_title = "Welcome to PropertySpotter Administration"