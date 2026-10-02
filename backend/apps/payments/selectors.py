from django.db import models
from apps.payments.models import Payment
from apps.diagnostics.models import CentreMembership


def get_payments_visible_to_user(user):
    """
    Returns queryset of Payment objects visible to the given user:
    - Platform Admin (superuser): All payments.
    - Clinic Admin: Payments for bookings belonging to centres they administer.
    - Patient / Normal user: Only payments for their own bookings.
    """
    if not user or user.is_anonymous or not user.is_authenticated:
        return Payment.objects.none()

    base_qs = Payment.objects.select_related(
        'booking',
        'booking__user',
        'booking__centre_test',
        'booking__centre_test__centre',
        'booking__centre_test__test',
        'booking__slot'
    )

    if user.is_superuser:
        return base_qs.all()

    admin_centre_ids = CentreMembership.objects.filter(
        user=user,
        role=CentreMembership.Role.ADMIN
    ).values_list('centre_id', flat=True)

    if admin_centre_ids.exists():
        return base_qs.filter(
            models.Q(booking__user=user) | models.Q(booking__centre_test__centre_id__in=admin_centre_ids)
        ).distinct()

    return base_qs.filter(booking__user=user)
