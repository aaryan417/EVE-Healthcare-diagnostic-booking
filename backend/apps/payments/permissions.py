from rest_framework import permissions
from apps.diagnostics.services import user_can_manage_centre


class IsPaymentOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class for Payment access:
    - Authentication required.
    - Patient can view payments for their own bookings.
    - Clinic Admin can view payments for bookings belonging to assigned centres.
    - Platform Admin can view all payments.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        if obj.booking.user == request.user:
            return True

        return user_can_manage_centre(request.user, obj.booking.centre_test.centre)
