from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from apps.bookings.models import Booking
from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)
from apps.diagnostics.serializers import (
    DiagnosticCentreSerializer,
    CentreMembershipSerializer,
    DiagnosticTestSerializer,
    CentreTestReadSerializer,
    CentreTestWriteSerializer,
    AppointmentSlotSerializer,
    BulkGenerateSlotsSerializer,
)
from apps.diagnostics.permissions import (
    IsCentreManagerOrReadOnly,
    IsPlatformAdmin,
    IsDiagnosticTestManagerOrReadOnly,
    IsCentreTestManagerOrReadOnly,
    IsAppointmentSlotManagerOrReadOnly,
)
from apps.diagnostics.services import (
    get_centres_visible_to_user,
    get_diagnostic_tests_visible_to_user,
    get_centre_tests_visible_to_user,
    get_slots_visible_to_user,
    get_available_dates_for_centre_test,
    user_can_manage_centre,
    bulk_generate_slots,
)


class DiagnosticCentreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DiagnosticCentres:
    - GET /api/v1/centres/
    - GET /api/v1/centres/<id>/
    - POST /api/v1/centres/ (Platform Admin only)
    - PATCH /api/v1/centres/<id>/ (Platform Admin or assigned Clinic Admin)
    """
    permission_classes = [IsCentreManagerOrReadOnly]
    serializer_class = DiagnosticCentreSerializer

    def get_queryset(self):
        return get_centres_visible_to_user(self.request.user)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed. Use PATCH to set is_active=false."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class CentreMembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for platform-admin-only CentreMembership management:
    - GET /api/v1/centre-memberships/
    - POST /api/v1/centre-memberships/
    - DELETE /api/v1/centre-memberships/<id>/
    """
    permission_classes = [IsPlatformAdmin]
    queryset = CentreMembership.objects.select_related('user', 'centre').all()
    serializer_class = CentreMembershipSerializer


class DiagnosticTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for global DiagnosticTest catalog:
    - GET /api/v1/tests/
    - GET /api/v1/tests/<id>/
    - POST /api/v1/tests/ (Platform Admin only)
    - PATCH /api/v1/tests/<id>/ (Platform Admin only)
    """
    permission_classes = [IsDiagnosticTestManagerOrReadOnly]
    serializer_class = DiagnosticTestSerializer

    def get_queryset(self):
        return get_diagnostic_tests_visible_to_user(self.request.user)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed. Use PATCH to set is_active=false."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class CentreTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for centre-specific Diagnostic Test offerings and pricing:
    - GET /api/v1/centre-tests/
    - GET /api/v1/centre-tests/?centre=<centre_id>
    - GET /api/v1/centre-tests/<id>/
    - POST /api/v1/centre-tests/
    - PATCH /api/v1/centre-tests/<id>/
    """
    permission_classes = [IsCentreTestManagerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CentreTestReadSerializer
        return CentreTestWriteSerializer

    def get_queryset(self):
        qs = get_centre_tests_visible_to_user(self.request.user)
        centre_id = self.request.query_params.get('centre')
        if centre_id:
            qs = qs.filter(centre_id=centre_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed. Use PATCH to set is_available=false."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class AppointmentSlotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for appointment slot availability and management:
    - GET /api/v1/slots/
    - GET /api/v1/slots/?centre_test=<id>&date=YYYY-MM-DD
    - GET /api/v1/slots/?centre=<centre_id>&date=YYYY-MM-DD
    - GET /api/v1/slots/available-dates/?centre_test=<id>
    - POST /api/v1/slots/
    - PATCH /api/v1/slots/<id>/
    """
    permission_classes = [IsAppointmentSlotManagerOrReadOnly]
    serializer_class = AppointmentSlotSerializer

    def get_queryset(self):
        qs = get_slots_visible_to_user(self.request.user)

        centre_test_id = self.request.query_params.get('centre_test')
        if centre_test_id:
            qs = qs.filter(centre_test_id=centre_test_id)

        centre_id = self.request.query_params.get('centre')
        if centre_id:
            qs = qs.filter(centre_test__centre_id=centre_id)

        slot_date = self.request.query_params.get('date')
        if slot_date:
            qs = qs.filter(date=slot_date)

        return qs.order_by('date', 'start_time')


    @action(detail=False, methods=['get'], url_path='available-dates', pagination_class=None)

    def available_dates(self, request):
        centre_test_id = request.query_params.get('centre_test')
        if not centre_test_id:
            return Response(
                {"detail": "Query parameter 'centre_test' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            centre_test_id_int = int(centre_test_id)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid 'centre_test' parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        dates = get_available_dates_for_centre_test(request.user, centre_test_id_int)
        return Response({
            "centre_test": centre_test_id_int,
            "dates": dates
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'DELETE' not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class CentreAdminProfileView(APIView):
    """
    GET /api/v1/centre-admin/me/
    Returns whether the current user is a centre admin and lists their assigned centres.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_superuser:
            centres = DiagnosticCentre.objects.filter(is_active=True)
            centres_data = [
                {"id": c.id, "name": c.name, "role": "ADMIN"}
                for c in centres
            ]
            return Response({
                "is_centre_admin": True,
                "centres": centres_data
            }, status=status.HTTP_200_OK)

        memberships = CentreMembership.objects.filter(
            user=user,
            role=CentreMembership.Role.ADMIN,
            centre__is_active=True
        ).select_related('centre')

        is_centre_admin = memberships.exists()
        centres_data = [
            {"id": m.centre.id, "name": m.centre.name, "role": m.role}
            for m in memberships
        ]

        return Response({
            "is_centre_admin": is_centre_admin,
            "centres": centres_data
        }, status=status.HTTP_200_OK)


class CentreAdminDashboardView(APIView):
    """
    GET /api/v1/centre-admin/dashboard/?centre=<id>
    Returns summary statistics and recent bookings scoped to an assigned centre.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        centre_id = request.query_params.get('centre')
        if not centre_id:
            return Response(
                {"detail": "Query parameter 'centre' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            centre = DiagnosticCentre.objects.get(id=centre_id)
        except (DiagnosticCentre.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Diagnostic centre not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not user_can_manage_centre(request.user, centre):
            return Response(
                {"detail": "You do not have permission to manage this centre."},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()

        active_tests_count = CentreTest.objects.filter(
            centre=centre,
            is_available=True,
            test__is_active=True
        ).count()

        today_bookings_count = Booking.objects.filter(
            centre_test__centre=centre,
            slot__date=today
        ).count()

        upcoming_bookings_count = Booking.objects.filter(
            centre_test__centre=centre,
            slot__date__gte=today,
            status__in=['PENDING', 'CONFIRMED']
        ).count()

        upcoming_slots_count = AppointmentSlot.objects.filter(
            centre_test__centre=centre,
            date__gte=today
        ).count()

        recent_bookings_qs = Booking.objects.filter(
            centre_test__centre=centre
        ).select_related('user', 'centre_test__test', 'slot').order_by('-created_at')[:5]

        recent_bookings = [
            {
                "id": b.id,
                "patient_name": b.user.name or b.user.email,
                "patient_email": b.user.email,
                "test_name": b.centre_test.test.name,
                "slot_date": b.slot.date.strftime('%Y-%m-%d'),
                "slot_time": f"{b.slot.start_time.strftime('%H:%M')} - {b.slot.end_time.strftime('%H:%M')}",
                "amount": str(b.amount),
                "status": b.status
            }
            for b in recent_bookings_qs
        ]

        return Response({
            "active_tests": active_tests_count,
            "today_bookings": today_bookings_count,
            "upcoming_bookings": upcoming_bookings_count,
            "upcoming_slots": upcoming_slots_count,
            "recent_bookings": recent_bookings
        }, status=status.HTTP_200_OK)


class CentreAdminBulkGenerateSlotsView(APIView):
    """
    POST /api/v1/centre-admin/slots/bulk-generate/
    Bulk generates appointment slots for a centre test offering across a date range and working hours.
    Requires user to be authenticated and an ADMIN for the centre owning centre_test.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        centre_test_id = request.data.get('centre_test')
        if centre_test_id is not None:
            try:
                ct = CentreTest.objects.select_related('centre').get(id=centre_test_id)
                if not user_can_manage_centre(request.user, ct.centre):
                    return Response(
                        {"detail": "You do not have permission to manage slots for this centre."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except (CentreTest.DoesNotExist, ValueError, TypeError):
                pass

        admin_memberships = CentreMembership.objects.filter(
            user=request.user,
            role=CentreMembership.Role.ADMIN
        )
        if not (request.user.is_superuser or admin_memberships.exists()):
            return Response(
                {"detail": "Only Centre Admins can bulk generate slots."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BulkGenerateSlotsSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        result = bulk_generate_slots(
            centre_test=data['centre_test_obj'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            slot_duration_minutes=data['slot_duration_minutes'],
            capacity=data['capacity'],
        )

        return Response(result, status=status.HTTP_201_CREATED)


