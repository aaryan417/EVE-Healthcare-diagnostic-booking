from rest_framework import permissions
from apps.diagnostics.models import DiagnosticCentre, CentreTest
from apps.diagnostics.services import user_can_manage_centre


class IsPlatformAdmin(permissions.BasePermission):
    """
    Permission class allowing access only to platform superusers (is_superuser=True).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsCentreManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class for DiagnosticCentre access:
    - Safe methods (GET, HEAD, OPTIONS): Allowed for any user (including anonymous).
    - POST (create new centre): Allowed ONLY for platform superusers (is_superuser=True).
    - PATCH/PUT (update existing centre): Allowed for platform superusers or clinic admins holding an ADMIN membership for the centre.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == 'POST':
            return bool(request.user.is_superuser)

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return user_can_manage_centre(request.user, obj)


class IsDiagnosticTestManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class for global DiagnosticTest catalog:
    - Safe methods (GET, HEAD, OPTIONS): Allowed for any user (including anonymous).
    - Write methods (POST, PATCH, PUT, DELETE): Allowed ONLY for platform superusers (is_superuser=True).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return bool(request.user.is_superuser)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsCentreTestManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class for CentreTest offerings:
    - Safe methods: Allowed for any user (including anonymous).
    - POST (create offering): Platform superusers OR clinic admins for a centre they manage.
    - PATCH/PUT (update offering): Platform superusers OR clinic admins for the centre offering belongs to.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == 'POST':
            if request.user.is_superuser:
                return True

            centre_id = request.data.get('centre')
            if not centre_id:
                return True

            try:
                centre = DiagnosticCentre.objects.get(id=centre_id)
                return user_can_manage_centre(request.user, centre)
            except (DiagnosticCentre.DoesNotExist, ValueError, TypeError):
                return True

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return user_can_manage_centre(request.user, obj.centre)


class IsAppointmentSlotManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class for AppointmentSlot management:
    - Safe methods: Allowed for any user (including anonymous).
    - POST: Platform superusers OR clinic admins for the centre offering belongs to.
    - PATCH/PUT: Platform superusers OR clinic admins for the centre offering belongs to.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == 'POST':
            if request.user.is_superuser:
                return True

            centre_test_id = request.data.get('centre_test')
            if not centre_test_id:
                return True

            try:
                centre_test = CentreTest.objects.select_related('centre').get(id=centre_test_id)
                return user_can_manage_centre(request.user, centre_test.centre)
            except (CentreTest.DoesNotExist, ValueError, TypeError):
                return True

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return user_can_manage_centre(request.user, obj.centre_test.centre)

