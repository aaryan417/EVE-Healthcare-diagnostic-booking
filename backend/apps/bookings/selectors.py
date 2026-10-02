from django.db import models
from apps.bookings.models import Booking
from apps.diagnostics.models import CentreMembership


def get_bookings_visible_to_user(user):
    """
    Returns queryset of Booking objects visible to the given user:
    - Platform Admin (superuser): All bookings.
    - Clinic Admin: Bookings for centres where they hold an ADMIN CentreMembership.
    - Patient / Normal user: Only their own bookings.
    """
    if not user or user.is_anonymous or not user.is_authenticated:
        return Booking.objects.none()

    base_qs = Booking.objects.select_related(
        'user',
        'centre_test',
        'centre_test__centre',
        'centre_test__test',
        'slot'
    )

    if user.is_superuser:
        return base_qs.all()

    admin_centre_ids = CentreMembership.objects.filter(
        user=user,
        role=CentreMembership.Role.ADMIN
    ).values_list('centre_id', flat=True)

    if admin_centre_ids.exists():
        return base_qs.filter(
            models.Q(user=user) | models.Q(centre_test__centre_id__in=admin_centre_ids)
        ).distinct()

    return base_qs.filter(user=user)
