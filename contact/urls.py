from django.urls import path
from .views import ContactEntryView

urlpatterns = [
    path('submit/', ContactEntryView.as_view(), name='contact-submit'),
] 