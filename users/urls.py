from django.urls import path
from .views import (
    UserRegistrationView, 
    EmailVerificationView, 
    AgencyCreateView,
    EmailLoginView,
    UserDetailView,
    UserProfileView,
    UserProfileUpdateView,
    AgencyListView,
    AgencyAgentsListView,
    DeactivateUserView,
    ReactivateUserView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)
from . import views

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('agency/create/', AgencyCreateView.as_view(), name='agency-create'),
    path('login/', EmailLoginView.as_view(), name='user-login'),
    path('<uuid:id>/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('agencies/', AgencyListView.as_view(), name='agency-list'),
    path('agencies/<uuid:agency_id>/agents/', AgencyAgentsListView.as_view(), name='agency-agents-list'),
    path('invite-agent/', views.AgentInvitationView.as_view(), name='invite-agent'),
    path('set-password/', views.SetPasswordView.as_view(), name='set-password'),
    path('<uuid:id>/deactivate/', DeactivateUserView.as_view(), name='deactivate-user'),
    path('<uuid:id>/reactivate/', ReactivateUserView.as_view(), name='reactivate-user'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
] 