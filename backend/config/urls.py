"""
URL configuration for EVE Healthcare project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.diagnostics.urls')),
    path('api/v1/', include('apps.bookings.urls')),
    path('api/v1/', include('apps.payments.urls')),
]

