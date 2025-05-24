from django.urls import path
from .views import (
    LeadSubmissionView,
    SpotterLeadsListView,
    AgencyLeadsListView
)

urlpatterns = [
    path('submit/', LeadSubmissionView.as_view(), name='lead-submit'),
    path('user/<str:user_id>/', SpotterLeadsListView.as_view(), name='spotter-leads'),
    path('agency/<str:agency_id>/', AgencyLeadsListView.as_view(), name='agency-leads'),
] 