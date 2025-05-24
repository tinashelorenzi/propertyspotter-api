from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.LeadSubmissionView.as_view(), name='lead-submit'),
    path('list/', views.LeadListView.as_view(), name='lead-list'),
    path('<int:id>/', views.LeadDetailView.as_view(), name='lead-detail'),
    path('<int:id>/assign/', views.LeadAssignmentView.as_view(), name='lead-assign'),
    path('agency/<uuid:agency_id>/', views.AgencyLeadsListView.as_view(), name='agency-leads-list'),
] 