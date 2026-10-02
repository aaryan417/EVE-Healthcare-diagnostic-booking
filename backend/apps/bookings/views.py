from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.models import Booking
from apps.bookings.serializers import (
    BookingReadSerializer,
    BookingCreateSerializer,
)
from apps.bookings.permissions import IsBookingOwnerOrAdmin
from apps.bookings.selectors import get_bookings_visible_to_user
from apps.bookings.services import create_booking, cancel_booking


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for booking operations:
    - POST /api/v1/bookings/ (Create PENDING booking)
    - GET /api/v1/bookings/ (List visible bookings)
    - GET /api/v1/bookings/<id>/ (Retrieve booking detail)
    - POST /api/v1/bookings/<id>/cancel/ (Cancel booking)
    """
    permission_classes = [IsBookingOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingReadSerializer

    def get_queryset(self):
        qs = get_bookings_visible_to_user(self.request.user)
        centre_id = self.request.query_params.get('centre')
        if centre_id:
            qs = qs.filter(centre_test__centre_id=centre_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(slot__date=date_param)
        test_id = self.request.query_params.get('test')
        if test_id:
            qs = qs.filter(centre_test__test_id=test_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slot_id = serializer.validated_data['slot']
        booking = create_booking(user=request.user, slot_id=slot_id)

        read_serializer = BookingReadSerializer(booking)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        booking = cancel_booking(user=request.user, booking_id=pk)
        read_serializer = BookingReadSerializer(booking)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct updates to bookings are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct updates to bookings are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed. Use POST /cancel/ to cancel a booking."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
