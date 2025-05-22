from django.urls import path
from .views import (
    UserRegistrationView, 
    EmailVerificationView, 
    AgencyCreateView,
    EmailLoginView,
    UserDetailView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('agency/create/', AgencyCreateView.as_view(), name='agency-create'),
    path('login/', EmailLoginView.as_view(), name='user-login'),
    path('<int:id>/', UserDetailView.as_view(), name='user-detail'),
] 