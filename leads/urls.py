from django.urls import path
from .views import LeadSubmissionView, SpotterLeadsListView

urlpatterns = [
    path('submit/', LeadSubmissionView.as_view(), name='lead-submit'),
    path('spotter/<str:user_id>/', SpotterLeadsListView.as_view(), name='spotter-leads'),
] 