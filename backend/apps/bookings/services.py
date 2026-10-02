from django.db import transaction, models
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.bookings.models import Booking
from apps.diagnostics.models import AppointmentSlot
from apps.diagnostics.services import user_can_manage_centre


class SlotFullException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This appointment slot is fully booked."
    default_code = "slot_full"


@transaction.atomic
def create_booking(user, slot_id: int) -> Booking:
    """
    Creates a PENDING booking in a concurrency-safe atomic transaction.
    Locks the AppointmentSlot row using select_for_update().
    Enforces parent active/available status, future slot date/time, user duplicate active booking check,
    and slot capacity limits. Snapshots CentreTest price into amount.
    """
    if not slot_id:
        raise ValidationError({"slot": "Appointment slot ID is required."})

    try:
        slot = AppointmentSlot.objects.select_for_update().select_related(
            'centre_test',
            'centre_test__centre',
            'centre_test__test'
        ).get(id=slot_id)
    except (AppointmentSlot.DoesNotExist, ValueError, TypeError):
        raise ValidationError({"slot": "Invalid appointment slot."})

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    # Revalidate parent active/availability status
    if not slot.centre_test.centre.is_active:
        raise ValidationError({"slot": "Diagnostic centre is inactive."})
    if not slot.centre_test.test.is_active:
        raise ValidationError({"slot": "Diagnostic test is inactive."})
    if not slot.centre_test.is_available:
        raise ValidationError({"slot": "Diagnostic test offering is unavailable."})

    # Revalidate future slot requirement
    if slot.date < current_date or (slot.date == current_date and slot.start_time <= current_time):
        raise ValidationError({"slot": "Cannot book an appointment slot in the past."})

    # Check for duplicate active booking by same user
    active_user_booking = Booking.objects.filter(
        user=user,
        slot=slot,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
    ).exists()
    if active_user_booking:
        raise ValidationError({"non_field_errors": ["You already have an active booking for this appointment slot."]})

    # Check slot capacity
    active_booking_count = Booking.objects.filter(
        slot=slot,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
    ).count()

    if active_booking_count >= slot.capacity:
        raise SlotFullException()

    booking = Booking.objects.create(
        user=user,
        centre_test=slot.centre_test,
        slot=slot,
        amount=slot.centre_test.price,
        status=Booking.Status.PENDING
    )
    return booking


@transaction.atomic
def cancel_booking(user, booking_id: int) -> Booking:
    """
    Cancels an existing eligible booking (PENDING -> CANCELLED or CONFIRMED -> CANCELLED).
    Sets cancelled_at timestamp to release capacity.
    """
    try:
        booking = Booking.objects.select_for_update().select_related(
            'user', 'centre_test', 'centre_test__centre', 'slot'
        ).get(id=booking_id)
    except (Booking.DoesNotExist, ValueError, TypeError):
        raise ValidationError({"detail": "Booking not found."})

    # Check permission
    is_owner = (booking.user == user)
    is_platform_admin = getattr(user, 'is_superuser', False)

    if not (is_owner or is_platform_admin):
        raise ValidationError({"detail": "You do not have permission to cancel this booking."})

    if booking.status in [Booking.Status.CANCELLED, Booking.Status.FAILED]:
        raise ValidationError({"detail": f"Booking in status '{booking.status}' cannot be cancelled."})

    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=['status', 'cancelled_at', 'updated_at'])
    return booking
