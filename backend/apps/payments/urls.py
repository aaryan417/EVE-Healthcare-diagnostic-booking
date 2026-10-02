from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentViewSet, WebhookView

app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('payments/webhook/', WebhookView.as_view(), name='payment_webhook'),
    path('', include(router.urls)),
]
