from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.bookings.models import Booking
from apps.diagnostics.models import (
    DiagnosticCentre,
    DiagnosticTest,
    AppointmentSlot,
)

User = get_user_model()


from apps.diagnostics.serializers import (
    UserMinimalSerializer,
    DiagnosticCentreMinimalSerializer,
    DiagnosticTestMinimalSerializer,
)



class SlotMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentSlot
        fields = ('id', 'date', 'start_time', 'end_time')
        read_only_fields = fields


class BookingReadSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    centre = DiagnosticCentreMinimalSerializer(source='centre_test.centre', read_only=True)
    test = DiagnosticTestMinimalSerializer(source='centre_test.test', read_only=True)
    slot = SlotMinimalSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id',
            'status',
            'amount',
            'user',
            'centre',
            'test',
            'slot',
            'created_at',
            'updated_at',
            'cancelled_at',
        )
        read_only_fields = fields


class BookingCreateSerializer(serializers.Serializer):
    slot = serializers.IntegerField(required=True)

    def validate_slot(self, value):
        if not value:
            raise serializers.ValidationError("Slot ID is required.")
        return value
