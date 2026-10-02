from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import RegisterView, LoginView, CurrentUserView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', CurrentUserView.as_view(), name='me'),
]
