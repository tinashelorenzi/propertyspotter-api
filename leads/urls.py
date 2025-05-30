from django.urls import path
from .views import (
    LeadSubmissionView,
    LeadListView,
    LeadDetailView,
    LeadAssignmentView,
    AgencyLeadsListView,
    AgentLeadsView,
    LeadAcceptanceView,
    LeadPropertyUpdateView,
    LeadWhatsAppNotificationView,
    LeadCompletionView,
    LeadFailureView,
    SpotterLeadsListView
)

urlpatterns = [
    path('submit/', LeadSubmissionView.as_view(), name='lead-submit'),
    path('list/', LeadListView.as_view(), name='lead-list'),
    path('<int:id>/', LeadDetailView.as_view(), name='lead-detail'),
    path('<int:id>/assign/', LeadAssignmentView.as_view(), name='lead-assign'),
    path('<int:id>/accept/', LeadAcceptanceView.as_view(), name='lead-accept'),
    path('<int:id>/property/', LeadPropertyUpdateView.as_view(), name='lead-property-update'),
    path('<int:id>/notify/', LeadWhatsAppNotificationView.as_view(), name='lead-whatsapp-notify'),
    path('<int:id>/complete/', LeadCompletionView.as_view(), name='lead-complete'),
    path('<int:id>/fail/', LeadFailureView.as_view(), name='lead-fail'),
    path('agency/<uuid:agency_id>/', AgencyLeadsListView.as_view(), name='agency-leads'),
    path('agent/<uuid:agent_id>/', AgentLeadsView.as_view(), name='agent-leads'),
    path('spotter/<uuid:spotter_id>/', SpotterLeadsListView.as_view(), name='spotter-leads'),
] 