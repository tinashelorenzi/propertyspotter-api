"""
URL configuration for propertyspotter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/users/', include('users.urls')),
    path('api/updates/', include('updates.urls')),
    path('api/leads/', include('leads.urls')),
    path('api/contact/', include('contact.urls')),
    path('api/listings/', include('listings.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),  # For CKEditor 5 file uploads
    path('blog/', include('blog.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
