from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.diagnostics.views import (
    DiagnosticCentreViewSet,
    CentreMembershipViewSet,
    DiagnosticTestViewSet,
    CentreTestViewSet,
    AppointmentSlotViewSet,
    CentreAdminProfileView,
    CentreAdminDashboardView,
    CentreAdminBulkGenerateSlotsView,
)

app_name = 'diagnostics'

router = DefaultRouter()
router.register(r'centres', DiagnosticCentreViewSet, basename='centre')
router.register(r'centre-memberships', CentreMembershipViewSet, basename='centre-membership')
router.register(r'tests', DiagnosticTestViewSet, basename='test')
router.register(r'centre-tests', CentreTestViewSet, basename='centre-test')
router.register(r'slots', AppointmentSlotViewSet, basename='slot')

urlpatterns = [
    path('centre-admin/me/', CentreAdminProfileView.as_view(), name='centre-admin-me'),
    path('centre-admin/dashboard/', CentreAdminDashboardView.as_view(), name='centre-admin-dashboard'),
    path('centre-admin/slots/bulk-generate/', CentreAdminBulkGenerateSlotsView.as_view(), name='centre-admin-slots-bulk-generate'),
    path('', include(router.urls)),
]

