from decimal import Decimal
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def patient_user():
    return User.objects.create_user(
        email="patient@example.com",
        password="Password123!",
        name="Patient User"
    )


@pytest.fixture
def platform_admin():
    return User.objects.create_superuser(
        email="platformadmin@example.com",
        password="AdminPassword123!",
        name="Platform Admin"
    )


@pytest.fixture
def clinic_admin_a():
    return User.objects.create_user(
        email="admin_a@clinic.com",
        password="Password123!",
        name="Clinic Admin A"
    )


@pytest.fixture
def centre_a():
    return DiagnosticCentre.objects.create(
        name="Centre A",
        address="Address A",
        city="City A",
        state="State A",
        pincode="100001",
        is_active=True
    )


@pytest.fixture
def centre_b():
    return DiagnosticCentre.objects.create(
        name="Centre B",
        address="Address B",
        city="City B",
        state="State B",
        pincode="100002",
        is_active=True
    )


@pytest.fixture
def diagnostic_test_1():
    return DiagnosticTest.objects.create(
        name="Complete Blood Count",
        description="CBC Test",
        is_active=True
    )


@pytest.fixture
def centre_test_a(centre_a, diagnostic_test_1):
    return CentreTest.objects.create(
        centre=centre_a,
        test=diagnostic_test_1,
        price=Decimal("500.00"),
        is_available=True
    )


@pytest.fixture
def centre_test_b(centre_b, diagnostic_test_1):
    return CentreTest.objects.create(
        centre=centre_b,
        test=diagnostic_test_1,
        price=Decimal("600.00"),
        is_available=True
    )


@pytest.mark.django_db
class TestSlotValidationAndCreation:

    # 5. end before start rejected
    def test_end_before_start_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {
            "centre_test": centre_test_a.id,
            "date": future_date,
            "start_time": "10:00:00",
            "end_time": "09:00:00",
            "capacity": 1
        }
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_time' in response.data

    # 6. end equal start rejected
    def test_end_equal_start_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {
            "centre_test": centre_test_a.id,
            "date": future_date,
            "start_time": "10:00:00",
            "end_time": "10:00:00",
            "capacity": 1
        }
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_time' in response.data

    # 8. overlapping slot rejected
    def test_overlapping_slot_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        future_date = future_date_obj.strftime('%Y-%m-%d')

        # Create 09:00 - 10:00
        AppointmentSlot.objects.create(
            centre_test=centre_test_a,
            date=future_date_obj,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )

        # Attempt 09:30 - 10:30
        payload = {
            "centre_test": centre_test_a.id,
            "date": future_date,
            "start_time": "09:30:00",
            "end_time": "10:30:00",
            "capacity": 1
        }
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 11. past date rejected
    def test_past_date_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)
        past_date = (timezone.now().date() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        payload = {
            "centre_test": centre_test_a.id,
            "date": past_date,
            "start_time": "09:00:00",
            "end_time": "10:00:00"
        }
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 13. future slot accepted
    def test_future_slot_accepted(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {
            "centre_test": centre_test_a.id,
            "date": future_date,
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "capacity": 5
        }
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['capacity'] == 5


@pytest.mark.django_db
class TestPatientSlotAPI:

    # 9. anonymous can GET future slots
    def test_anonymous_can_get_future_slots(self, api_client, centre_test_a):
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(
            centre_test=centre_test_a,
            date=future_date_obj,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=2
        )
        response = api_client.get('/api/v1/slots/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert slot.id in slot_ids

    # 10. anonymous cannot see unavailable/full/past slots
    def test_anonymous_cannot_see_unavailable_full_or_past_slots(self, api_client, patient_user, centre_test_a, diagnostic_test_1):
        past_date = timezone.now().date() - datetime.timedelta(days=1)
        future_date = timezone.now().date() + datetime.timedelta(days=3)

        past_slot = AppointmentSlot.objects.create(centre_test=centre_test_a, date=past_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        full_slot = AppointmentSlot.objects.create(centre_test=centre_test_a, date=future_date, start_time=datetime.time(11, 0), end_time=datetime.time(12, 0), capacity=1)
        # Create booking for full_slot to fill capacity
        from apps.bookings.models import Booking
        Booking.objects.create(
            user=patient_user,
            centre_test=centre_test_a,
            slot=full_slot,
            amount=centre_test_a.price,
            status='CONFIRMED'
        )

        response = api_client.get('/api/v1/slots/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert past_slot.id not in slot_ids
        assert full_slot.id not in slot_ids

    # 17. anonymous cannot POST appointment slot
    def test_anonymous_cannot_post_appointment_slot(self, api_client, centre_test_a):
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {"centre_test": centre_test_a.id, "date": future_date, "start_time": "09:00:00", "end_time": "10:00:00"}
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 18. anonymous cannot PATCH appointment slot
    def test_anonymous_cannot_patch_appointment_slot(self, api_client, centre_test_a):
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=centre_test_a, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        payload = {"capacity": 10}
        response = api_client.patch(f'/api/v1/slots/{slot.id}/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 14. authenticated patient can list future slots
    def test_authenticated_patient_can_list_future_slots(self, api_client, patient_user, centre_test_a):
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(
            centre_test=centre_test_a,
            date=future_date_obj,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/slots/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert slot.id in slot_ids

    # 16. patient can filter by centre_test
    def test_patient_can_filter_by_centre_test(self, api_client, patient_user, centre_test_a, centre_test_b):
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        s_a = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        s_b = AppointmentSlot.objects.create(
            centre_test=centre_test_b, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/slots/?centre_test={centre_test_a.id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert s_a.id in slot_ids
        assert s_b.id not in slot_ids

    # 17. patient can filter by date
    def test_patient_can_filter_by_date(self, api_client, patient_user, centre_test_a):
        date1 = timezone.now().date() + datetime.timedelta(days=3)
        date2 = timezone.now().date() + datetime.timedelta(days=5)
        s1 = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=date1, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        s2 = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=date2, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/slots/?date={date1.strftime("%Y-%m-%d")}')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert s1.id in slot_ids
        assert s2.id not in slot_ids

    # 20. inactive centre slots hidden
    def test_inactive_centre_slots_hidden(self, api_client, patient_user, diagnostic_test_1):
        inactive_c = DiagnosticCentre.objects.create(name="Inactive Lab", address="A", city="C", state="S", pincode="123", is_active=False)
        ct = CentreTest.objects.create(centre=inactive_c, test=diagnostic_test_1, price=Decimal("500"))
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/slots/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        slot_ids = [s['id'] for s in results]
        assert slot.id not in slot_ids

    # 23. patient cannot create slot
    def test_patient_cannot_create_slot(self, api_client, patient_user, centre_test_a):
        api_client.force_authenticate(user=patient_user)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {"centre_test": centre_test_a.id, "date": future_date, "start_time": "09:00:00", "end_time": "10:00:00"}
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCalendarAvailabilityAPI:

    # 8. anonymous can GET available dates
    def test_anonymous_can_get_available_dates(self, api_client, centre_test_a):
        d1 = timezone.now().date() + datetime.timedelta(days=3)
        AppointmentSlot.objects.create(centre_test=centre_test_a, date=d1, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        response = api_client.get(f'/api/v1/slots/available-dates/?centre_test={centre_test_a.id}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['centre_test'] == centre_test_a.id
        assert d1.strftime('%Y-%m-%d') in response.data['dates']

    # 25. available-dates returns unique dates sorted ascending
    def test_available_dates_returns_unique_dates_sorted(self, api_client, patient_user, centre_test_a):
        d1 = timezone.now().date() + datetime.timedelta(days=5)
        d2 = timezone.now().date() + datetime.timedelta(days=3)

        AppointmentSlot.objects.create(centre_test=centre_test_a, date=d1, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        AppointmentSlot.objects.create(centre_test=centre_test_a, date=d1, start_time=datetime.time(10, 0), end_time=datetime.time(11, 0))
        AppointmentSlot.objects.create(centre_test=centre_test_a, date=d2, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/slots/available-dates/?centre_test={centre_test_a.id}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['centre_test'] == centre_test_a.id
        dates = response.data['dates']
        assert dates == [d2.strftime('%Y-%m-%d'), d1.strftime('%Y-%m-%d')]

    # 29. invalid centre_test handled cleanly
    def test_invalid_centre_test_handled_cleanly(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/slots/available-dates/?centre_test=invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestClinicAdminAndTenantIsolation:

    # 30. clinic admin can create slot for assigned centre
    def test_clinic_admin_can_create_slot_assigned_centre(self, api_client, clinic_admin_a, centre_a, centre_test_a):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {"centre_test": centre_test_a.id, "date": future_date, "start_time": "09:00:00", "end_time": "10:00:00"}
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    # 31. clinic admin cannot create slot for unassigned centre
    def test_clinic_admin_cannot_create_slot_unassigned_centre(self, api_client, clinic_admin_a, centre_a, centre_test_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        future_date = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        payload = {"centre_test": centre_test_b.id, "date": future_date, "start_time": "09:00:00", "end_time": "10:00:00"}
        response = api_client.post('/api/v1/slots/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 34. cannot change centre_test identity
    def test_cannot_change_centre_test_identity(self, api_client, clinic_admin_a, centre_a, centre_test_a, centre_test_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        slot_a = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"centre_test": centre_test_b.id}
        response = api_client.patch(f'/api/v1/slots/{slot_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 38 & 39. MANDATORY TENANT ISOLATION TEST (Section 16)
    def test_section_16_mandatory_slot_tenant_isolation(
        self, api_client, clinic_admin_a, centre_a, centre_b, centre_test_a, centre_test_b
    ):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)

        future_date_obj = timezone.now().date() + datetime.timedelta(days=3)
        future_date = future_date_obj.strftime('%Y-%m-%d')

        slot_a = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        slot_b = AppointmentSlot.objects.create(
            centre_test=centre_test_b, date=future_date_obj, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )

        api_client.force_authenticate(user=clinic_admin_a)

        # POST slot for Centre A => SUCCESS
        res_create_a = api_client.post('/api/v1/slots/', {"centre_test": centre_test_a.id, "date": future_date, "start_time": "11:00:00", "end_time": "12:00:00"}, format='json')
        assert res_create_a.status_code == status.HTTP_201_CREATED

        # POST slot for Centre B => FAIL
        res_create_b = api_client.post('/api/v1/slots/', {"centre_test": centre_test_b.id, "date": future_date, "start_time": "11:00:00", "end_time": "12:00:00"}, format='json')
        assert res_create_b.status_code == status.HTTP_403_FORBIDDEN

        # PATCH Slot A => SUCCESS
        res_update_a = api_client.patch(f'/api/v1/slots/{slot_a.id}/', {"capacity": 10}, format='json')
        assert res_update_a.status_code == status.HTTP_200_OK

        # PATCH Slot B => FAIL
        res_update_b = api_client.patch(f'/api/v1/slots/{slot_b.id}/', {"capacity": 10}, format='json')
        assert res_update_b.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
