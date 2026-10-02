from rest_framework import permissions
from apps.diagnostics.services import user_can_manage_centre


class IsBookingOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class for Booking access:
    - Authentication is strictly required.
    - Patient can view/cancel their own booking.
    - Clinic Admin can view bookings belonging to a centre they manage.
    - Platform Admin can view and cancel any booking.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        if obj.user == request.user:
            return True

        return user_can_manage_centre(request.user, obj.centre_test.centre)
