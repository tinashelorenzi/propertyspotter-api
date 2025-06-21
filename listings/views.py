from django.shortcuts import render
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import PropertyListing, PropertyImage
from .serializers import (
    PropertyListingListSerializer,
    PropertyListingDetailSerializer,
    PropertyListingCreateSerializer,
    PropertyListingUpdateSerializer,
    PropertyImageUploadSerializer
)
import logging

logger = logging.getLogger(__name__)

class PropertyListingListView(generics.ListAPIView):
    """View for listing all active property listings"""
    queryset = PropertyListing.objects.filter(is_active=True)
    serializer_class = PropertyListingListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['province', 'suburb', 'property_type', 'bedrooms', 'bathrooms', 'is_pet_friendly', 'has_pool', 'is_featured']
    search_fields = ['title', 'description', 'suburb', 'street_address']
    ordering_fields = ['listing_price', 'bedrooms', 'bathrooms', 'published_at', 'view_count']
    ordering = ['-published_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by price range if provided
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(listing_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(listing_price__lte=max_price)
        
        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'results': serializer.data,
                'message': 'Property listings retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error fetching property listings: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching property listings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyListingDetailView(generics.RetrieveAPIView):
    """View for detailed property listing"""
    queryset = PropertyListing.objects.filter(is_active=True)
    serializer_class = PropertyListingDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.increment_view_count()  # Increment view count
            serializer = self.get_serializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data,
                'message': 'Property details retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error fetching property details: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching property details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyListingCreateView(generics.CreateAPIView):
    """View for creating new property listings"""
    serializer_class = PropertyListingCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            property_listing = serializer.save()
            
            logger.info(f"Property listing created: {property_listing.title} by {request.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Property listing created successfully',
                'data': PropertyListingDetailSerializer(property_listing, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating property listing: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while creating the property listing'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyListingUpdateView(generics.UpdateAPIView):
    """View for updating property listings"""
    queryset = PropertyListing.objects.all()
    serializer_class = PropertyListingUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Users can update listings they created or if they're admin
        if self.request.user.is_staff:
            return PropertyListing.objects.all()
        return PropertyListing.objects.filter(agent=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            property_listing = serializer.save()
            
            logger.info(f"Property listing updated: {property_listing.title} by {request.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Property listing updated successfully',
                'data': PropertyListingDetailSerializer(property_listing, context={'request': request}).data
            })
        except Exception as e:
            logger.error(f"Error updating property listing: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while updating the property listing'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyListingDeleteView(generics.DestroyAPIView):
    """View for deleting property listings"""
    queryset = PropertyListing.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Users can delete listings they created or if they're admin
        if self.request.user.is_staff:
            return PropertyListing.objects.all()
        return PropertyListing.objects.filter(agent=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            title = instance.title
            instance.delete()
            
            logger.info(f"Property listing deleted: {title} by {request.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Property listing deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting property listing: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while deleting the property listing'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FeaturedPropertyListView(generics.ListAPIView):
    """View for listing featured properties"""
    queryset = PropertyListing.objects.filter(is_active=True, is_featured=True)
    serializer_class = PropertyListingListSerializer
    permission_classes = [AllowAny]
    ordering = ['-published_at']

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'results': serializer.data,
                'message': 'Featured properties retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error fetching featured properties: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching featured properties'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyImageUploadView(generics.CreateAPIView):
    """View for uploading additional images to a property"""
    serializer_class = PropertyImageUploadSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            property_id = self.kwargs.get('property_id')
            property_listing = get_object_or_404(PropertyListing, id=property_id)
            
            # Check permissions - users can upload to their own listings or if they're admin
            if not request.user.is_staff and property_listing.agent != request.user:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to upload images to this property'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(data=request.data, context={'property_id': property_id})
            serializer.is_valid(raise_exception=True)
            property_image = serializer.save()
            
            logger.info(f"Image uploaded for property: {property_listing.title} by {request.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Image uploaded successfully',
                'data': {
                    'id': property_image.id,
                    'image_url': request.build_absolute_uri(property_image.image.url) if property_image.image else None,
                    'alt_text': property_image.alt_text,
                    'is_primary': property_image.is_primary
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error uploading property image: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while uploading the image'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
