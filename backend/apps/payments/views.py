from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentReadSerializer,
    PaymentCreateSerializer,
    WebhookEventSerializer,
)
from apps.payments.permissions import IsPaymentOwnerOrAdmin
from apps.payments.selectors import get_payments_visible_to_user
from apps.payments.services import process_payment, process_payment_webhook


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for simulated payment processing and historical payment retrieval:
    - POST /api/v1/payments/ (Simulate payment SUCCESS or FAILED)
    - GET /api/v1/payments/ (List visible payments)
    - GET /api/v1/payments/<id>/ (Retrieve payment detail)
    """
    permission_classes = [IsPaymentOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentReadSerializer

    def get_queryset(self):
        return get_payments_visible_to_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_id = serializer.validated_data['booking']
        simulate_result = serializer.validated_data.get('simulate_result', 'SUCCESS')

        payment = process_payment(
            user=request.user,
            booking_id=booking_id,
            simulate_result=simulate_result
        )

        read_serializer = PaymentReadSerializer(payment)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct updates to payment records are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct updates to payment records are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed on payment records."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class WebhookView(APIView):
    """
    POST /api/v1/payments/webhook/
    Process payment gateway webhook events with strict idempotency.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WebhookEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = process_payment_webhook(
            event_id=serializer.validated_data['event_id'],
            event_type=serializer.validated_data['event_type'],
            transaction_id=serializer.validated_data['transaction_id'],
            status_str=serializer.validated_data['status'],
            payload=request.data
        )
        return Response(result, status=status.HTTP_200_OK)

