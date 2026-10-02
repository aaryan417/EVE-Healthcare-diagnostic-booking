from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.bookings.views import BookingViewSet

app_name = 'bookings'

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]
