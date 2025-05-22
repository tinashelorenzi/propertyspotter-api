from django.urls import path
from .views import UpdateCreateView, UserUpdatesListView

urlpatterns = [
    path('create/', UpdateCreateView.as_view(), name='update-create'),
    path('user/<uuid:user_id>/', UserUpdatesListView.as_view(), name='user-updates'),
] 