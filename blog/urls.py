from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # API endpoints
    path('api/posts/', views.PublicBlogPostListView.as_view(), name='api_post_list'),
    path('api/posts/<slug:slug>/', views.PublicBlogPostDetailView.as_view(), name='api_post_detail'),
    # HTML views
    path('', views.post_list, name='post_list'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
] 