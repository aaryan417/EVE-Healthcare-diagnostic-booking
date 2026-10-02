from rest_framework import serializers
from apps.payments.models import Payment, WebhookEvent


class PaymentReadSerializer(serializers.ModelSerializer):
    booking = serializers.IntegerField(source='booking.id', read_only=True)
    booking_status = serializers.CharField(source='booking.status', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id',
            'transaction_id',
            'booking',
            'amount',
            'status',
            'created_at',
            'booking_status',
        )
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    booking = serializers.IntegerField(required=True)
    simulate_result = serializers.ChoiceField(
        choices=['SUCCESS', 'FAILED'],
        default='SUCCESS'
    )

    def validate_booking(self, value):
        if not value:
            raise serializers.ValidationError("Booking ID is required.")
        return value


class WebhookEventSerializer(serializers.Serializer):
    event_id = serializers.CharField(required=True, allow_blank=False)
    event_type = serializers.CharField(required=True, allow_blank=False)
    transaction_id = serializers.CharField(required=True, allow_blank=False)
    status = serializers.ChoiceField(choices=['SUCCESS', 'FAILED'], required=True)

    def validate_event_id(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("event_id cannot be blank.")
        return value.strip()

    def validate_event_type(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("event_type cannot be blank.")
        return value.strip()

    def validate_transaction_id(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("transaction_id cannot be blank.")
        return value.strip()

