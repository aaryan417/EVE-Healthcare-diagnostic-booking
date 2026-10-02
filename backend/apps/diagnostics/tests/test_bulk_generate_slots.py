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
        email="patient_test@example.com",
        password="Password123!",
        name="Patient User"
    )


@pytest.fixture
def platform_admin():
    return User.objects.create_superuser(
        email="platformadmin_test@example.com",
        password="AdminPassword123!",
        name="Platform Admin"
    )


@pytest.fixture
def centre_admin_a():
    return User.objects.create_user(
        email="admin_a_bulk@clinic.com",
        password="Password123!",
        name="Clinic Admin A"
    )


@pytest.fixture
def centre_admin_b():
    return User.objects.create_user(
        email="admin_b_bulk@clinic.com",
        password="Password123!",
        name="Clinic Admin B"
    )


@pytest.fixture
def centre_a():
    return DiagnosticCentre.objects.create(
        name="Bulk Centre A",
        address="Address A",
        city="City A",
        state="State A",
        pincode="100001",
        is_active=True
    )


@pytest.fixture
def centre_b():
    return DiagnosticCentre.objects.create(
        name="Bulk Centre B",
        address="Address B",
        city="City B",
        state="State B",
        pincode="100002",
        is_active=True
    )


@pytest.fixture
def diagnostic_test_1():
    return DiagnosticTest.objects.create(
        name="Complete Blood Count Bulk Test",
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
class TestBulkSlotGenerationAPI:

    # 1. Centre Admin can bulk generate slots for assigned centre
    def test_centre_admin_can_bulk_generate_slots_for_assigned_centre(
        self, api_client, centre_admin_a, centre_a, centre_test_a
    ):
        CentreMembership.objects.create(user=centre_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=centre_admin_a)

        start_d = (timezone.now().date() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_d = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 8  # 2 days * 4 slots/day
        assert response.data['skipped_count'] == 0
        assert response.data['date_count'] == 2

    # 2. Patient cannot bulk generate slots
    def test_patient_cannot_bulk_generate_slots(self, api_client, patient_user, centre_test_a):
        api_client.force_authenticate(user=patient_user)
        start_d = (timezone.now().date() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_d = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 3. Unauthenticated user gets rejected
    def test_unauthenticated_user_gets_rejected(self, api_client, centre_test_a):
        start_d = (timezone.now().date() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_d = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 4. Centre Admin cannot generate slots for another centre
    def test_centre_admin_cannot_generate_slots_for_another_centre(
        self, api_client, centre_admin_a, centre_a, centre_test_b
    ):
        CentreMembership.objects.create(user=centre_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=centre_admin_a)

        start_d = (timezone.now().date() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_d = (timezone.now().date() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')

        payload = {
            "centre_test": centre_test_b.id,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 5. Multiple dates generate correctly
    def test_multiple_dates_generate_correctly(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        start_d_obj = timezone.now().date() + datetime.timedelta(days=2)
        end_d_obj = start_d_obj + datetime.timedelta(days=4)  # 5 days total

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d_obj.strftime('%Y-%m-%d'),
            "end_date": end_d_obj.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:00",
            "slot_duration_minutes": 30,
            "capacity": 3
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 10  # 5 days * 2 slots/day
        assert response.data['date_count'] == 5

        # Verify DB records
        created_slots = AppointmentSlot.objects.filter(centre_test=centre_test_a)
        assert created_slots.count() == 10
        unique_dates = set(created_slots.values_list('date', flat=True))
        assert len(unique_dates) == 5


    # 6. Slot duration generates correct intervals
    def test_slot_duration_generates_correct_intervals(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_date = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_date.strftime('%Y-%m-%d'),
            "end_date": target_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 4

        intervals = list(
            AppointmentSlot.objects.filter(centre_test=centre_test_a, date=target_date)
            .order_by('start_time')
            .values_list('start_time', 'end_time')
        )

        expected = [
            (datetime.time(9, 0), datetime.time(9, 30)),
            (datetime.time(9, 30), datetime.time(10, 0)),
            (datetime.time(10, 0), datetime.time(10, 30)),
            (datetime.time(10, 30), datetime.time(11, 0)),
        ]
        assert intervals == expected

    # 7. Slot exceeding working end time is not created
    def test_slot_exceeding_working_end_time_not_created(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_date = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_date.strftime('%Y-%m-%d'),
            "end_date": target_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:00",
            "slot_duration_minutes": 45,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 1

        slots = list(AppointmentSlot.objects.filter(centre_test=centre_test_a, date=target_date))
        assert len(slots) == 1
        assert slots[0].start_time == datetime.time(9, 0)
        assert slots[0].end_time == datetime.time(9, 45)

    # 8. Existing exact duplicate is skipped
    def test_existing_exact_duplicate_is_skipped(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_date = timezone.now().date() + datetime.timedelta(days=2)

        # Pre-create 09:30 - 10:00
        AppointmentSlot.objects.create(
            centre_test=centre_test_a,
            date=target_date,
            start_time=datetime.time(9, 30),
            end_time=datetime.time(10, 0),
            capacity=5
        )

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_date.strftime('%Y-%m-%d'),
            "end_date": target_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:30",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 2  # 09:00-09:30, 10:00-10:30
        assert response.data['skipped_count'] == 1  # 09:30-10:00 skipped

    # 9. Existing overlapping slot is skipped
    def test_existing_overlapping_slot_is_skipped(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_date = timezone.now().date() + datetime.timedelta(days=2)

        # Pre-create overlapping slot 09:15 - 09:45
        AppointmentSlot.objects.create(
            centre_test=centre_test_a,
            date=target_date,
            start_time=datetime.time(9, 15),
            end_time=datetime.time(9, 45),
            capacity=5
        )

        # Request 09:00 - 10:30 with 30-min slots (candidates: 09:00-09:30, 09:30-10:00, 10:00-10:30)
        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_date.strftime('%Y-%m-%d'),
            "end_date": target_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:30",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['created_count'] == 1  # 10:00-10:30
        assert response.data['skipped_count'] == 2  # 09:00-09:30 and 09:30-10:00 both overlap with 09:15-09:45

    # 10. Running identical bulk request twice does not create duplicates
    def test_running_identical_bulk_request_twice_does_not_create_duplicates(
        self, api_client, platform_admin, centre_test_a
    ):
        api_client.force_authenticate(user=platform_admin)

        target_date = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_date.strftime('%Y-%m-%d'),
            "end_date": target_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        # 1st run
        res1 = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert res1.status_code == status.HTTP_201_CREATED
        assert res1.data['created_count'] == 4
        assert res1.data['skipped_count'] == 0

        # 2nd run
        res2 = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert res2.status_code == status.HTTP_201_CREATED
        assert res2.data['created_count'] == 0
        assert res2.data['skipped_count'] == 4

        # DB check
        assert AppointmentSlot.objects.filter(centre_test=centre_test_a, date=target_date).count() == 4

    # 11. Invalid start/end date rejected
    def test_invalid_start_end_date_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        start_d = timezone.now().date() + datetime.timedelta(days=5)
        end_d = timezone.now().date() + datetime.timedelta(days=2)  # end < start

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d.strftime('%Y-%m-%d'),
            "end_date": end_d.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_date' in response.data

    # 12. Past dates rejected
    def test_past_dates_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        past_d = timezone.now().date() - datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": past_d.strftime('%Y-%m-%d'),
            "end_date": past_d.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'start_date' in response.data

    # 13. start_time >= end_time rejected
    def test_start_time_gte_end_time_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_d = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_d.strftime('%Y-%m-%d'),
            "end_date": target_d.strftime('%Y-%m-%d'),
            "start_time": "11:00",
            "end_time": "09:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_time' in response.data

    # 14. zero/negative duration rejected
    def test_zero_or_negative_duration_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_d = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_d.strftime('%Y-%m-%d'),
            "end_date": target_d.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 0,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'slot_duration_minutes' in response.data

    # 15. zero/negative capacity rejected
    def test_zero_or_negative_capacity_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        target_d = timezone.now().date() + datetime.timedelta(days=2)

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": target_d.strftime('%Y-%m-%d'),
            "end_date": target_d.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": -1
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'capacity' in response.data

    # 16. excessive date range rejected
    def test_excessive_date_range_rejected(self, api_client, platform_admin, centre_test_a):
        api_client.force_authenticate(user=platform_admin)

        start_d = timezone.now().date() + datetime.timedelta(days=1)
        end_d = start_d + datetime.timedelta(days=35)  # 36 days > 31

        payload = {
            "centre_test": centre_test_a.id,
            "start_date": start_d.strftime('%Y-%m-%d'),
            "end_date": end_d.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "11:00",
            "slot_duration_minutes": 30,
            "capacity": 5
        }

        response = api_client.post('/api/v1/centre-admin/slots/bulk-generate/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_date' in response.data

    # 17. existing single-slot creation still works
    def test_existing_single_slot_creation_still_works(self, api_client, platform_admin, centre_test_a):
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
