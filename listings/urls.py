from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # Public endpoints
    path('properties/', views.PropertyListingListView.as_view(), name='property-list'),
    path('properties/featured/', views.FeaturedPropertyListView.as_view(), name='featured-properties'),
    path('properties/<uuid:id>/', views.PropertyListingDetailView.as_view(), name='property-detail'),
    
    # Agent endpoints (require authentication)
    path('properties/create/', views.PropertyListingCreateView.as_view(), name='property-create'),
    path('properties/<uuid:id>/update/', views.PropertyListingUpdateView.as_view(), name='property-update'),
    path('properties/<uuid:id>/delete/', views.PropertyListingDeleteView.as_view(), name='property-delete'),
    path('properties/<uuid:property_id>/images/', views.PropertyImageUploadView.as_view(), name='property-image-upload'),
] 