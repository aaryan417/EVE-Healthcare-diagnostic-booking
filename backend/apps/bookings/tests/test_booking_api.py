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
from apps.bookings.models import Booking

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def patient_a():
    return User.objects.create_user(
        email="patienta@example.com", password="Password123!", name="Patient A"
    )


@pytest.fixture
def patient_b():
    return User.objects.create_user(
        email="patientb@example.com", password="Password123!", name="Patient B"
    )


@pytest.fixture
def platform_admin():
    return User.objects.create_superuser(
        email="admin@example.com", password="AdminPassword123!", name="Platform Admin"
    )


@pytest.fixture
def clinic_admin_a():
    return User.objects.create_user(
        email="admin_a@clinic.com", password="Password123!", name="Clinic Admin A"
    )


@pytest.fixture
def staff_no_membership():
    return User.objects.create_user(
        email="staff_no_membership@clinic.com", password="Password123!", name="Staff User", is_staff=True
    )


@pytest.fixture
def centre_a():
    return DiagnosticCentre.objects.create(
        name="Centre A", address="Address A", city="City A", state="State A", pincode="100001", is_active=True
    )


@pytest.fixture
def centre_b():
    return DiagnosticCentre.objects.create(
        name="Centre B", address="Address B", city="City B", state="State B", pincode="100002", is_active=True
    )


@pytest.fixture
def test_1():
    return DiagnosticTest.objects.create(name="CBC Test", is_active=True)


@pytest.fixture
def centre_test_a(centre_a, test_1):
    return CentreTest.objects.create(centre=centre_a, test=test_1, price=Decimal("500.00"), is_available=True)


@pytest.fixture
def centre_test_b(centre_b, test_1):
    return CentreTest.objects.create(centre=centre_b, test=test_1, price=Decimal("650.00"), is_available=True)


@pytest.fixture
def slot_a(centre_test_a):
    future_date = timezone.now().date() + datetime.timedelta(days=3)
    return AppointmentSlot.objects.create(
        centre_test=centre_test_a, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), capacity=1
    )


@pytest.fixture
def slot_b(centre_test_b):
    future_date = timezone.now().date() + datetime.timedelta(days=3)
    return AppointmentSlot.objects.create(
        centre_test=centre_test_b, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), capacity=1
    )


@pytest.mark.django_db
class TestBookingCreationAPI:

    # 19. anonymous cannot create booking
    def test_anonymous_booking_creation_rejected(self, api_client, slot_a):
        response = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 20. anonymous cannot access My Bookings
    def test_anonymous_cannot_access_my_bookings(self, api_client):
        response = api_client.get('/api/v1/bookings/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 9, 10, 11. patient create booking, uses user & price snapshot
    def test_patient_can_create_booking_and_snapshots_price(self, api_client, patient_a, slot_a, centre_test_a):
        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == "PENDING"
        assert response.data['amount'] == "500.00"
        assert response.data['user']['id'] == patient_a.id

    # 12, 13, 14. client-supplied user/amount/status cannot manipulate creation
    def test_client_supplied_fields_ignored(self, api_client, patient_a, patient_b, slot_a):
        api_client.force_authenticate(user=patient_a)
        payload = {
            "slot": slot_a.id,
            "amount": "1.00",
            "user": patient_b.id,
            "status": "CONFIRMED"
        }
        response = api_client.post('/api/v1/bookings/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == "500.00"
        assert response.data['user']['id'] == patient_a.id
        assert response.data['status'] == "PENDING"

    # 15. inactive centre booking rejected
    def test_inactive_centre_booking_rejected(self, api_client, patient_a, test_1):
        inactive_c = DiagnosticCentre.objects.create(name="Inc", address="A", city="C", state="S", pincode="123", is_active=False)
        ct = CentreTest.objects.create(centre=inactive_c, test=test_1, price=Decimal("500.00"))
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 19. full capacity returns conflict (HTTP 409)
    def test_full_capacity_returns_conflict(self, api_client, patient_a, patient_b, slot_a):
        # Patient A books slot (capacity 1)
        api_client.force_authenticate(user=patient_a)
        res1 = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res1.status_code == status.HTTP_201_CREATED

        # Patient B attempts booking same slot
        api_client.force_authenticate(user=patient_b)
        res2 = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res2.status_code == status.HTTP_409_CONFLICT
        assert res2.data['detail'] == "This appointment slot is fully booked."

    # 25. same user cannot create second active booking for same slot
    def test_same_user_duplicate_active_booking_rejected(self, api_client, patient_a, centre_test_a):
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(
            centre_test=centre_test_a, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), capacity=5
        )
        api_client.force_authenticate(user=patient_a)
        res1 = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert res1.status_code == status.HTTP_201_CREATED

        res2 = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    # 26. same user can rebook after cancellation if capacity exists
    def test_user_rebook_after_cancellation(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res1 = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res1.data['id']

        # Cancel booking
        api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')

        # Rebook
        res2 = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res2.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestPriceSnapshot:

    # 23. MANDATORY PRICE SNAPSHOT TEST
    def test_price_snapshot_preserved_on_catalogue_price_change(self, api_client, patient_a, slot_a, centre_test_a):
        assert centre_test_a.price == Decimal("500.00")

        # Create booking
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        booking_id = res.data['id']
        assert res.data['amount'] == "500.00"

        # Change CentreTest price to 600.00
        centre_test_a.price = Decimal("600.00")
        centre_test_a.save()

        # Fetch booking again
        res_get = api_client.get(f'/api/v1/bookings/{booking_id}/')
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.data['amount'] == "500.00"  # STILL 500.00


@pytest.mark.django_db
class TestBookingVisibilityAndSecurity:

    # 27, 28, 29. Patient A vs Patient B visibility
    def test_patient_visibility_isolation(self, api_client, patient_a, patient_b, slot_a, slot_b):
        api_client.force_authenticate(user=patient_a)
        res_a = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_a_id = res_a.data['id']

        api_client.force_authenticate(user=patient_b)
        res_b = api_client.post('/api/v1/bookings/', {"slot": slot_b.id}, format='json')
        booking_b_id = res_b.data['id']

        # Patient A lists bookings -> sees only booking A
        api_client.force_authenticate(user=patient_a)
        res_list = api_client.get('/api/v1/bookings/')
        results = res_list.data['results'] if isinstance(res_list.data, dict) and 'results' in res_list.data else res_list.data
        b_ids = [b['id'] for b in results]
        assert booking_a_id in b_ids
        assert booking_b_id not in b_ids

        # Patient A cannot retrieve Patient B booking (404)
        res_get_b = api_client.get(f'/api/v1/bookings/{booking_b_id}/')
        assert res_get_b.status_code == status.HTTP_404_NOT_FOUND

    # 30, 31, 32, 33, 34. Clinic Admin & Platform Admin visibility
    def test_clinic_admin_and_platform_admin_visibility(
        self, api_client, patient_a, patient_b, clinic_admin_a, staff_no_membership, platform_admin, centre_a, slot_a, slot_b
    ):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)

        api_client.force_authenticate(user=patient_a)
        res_a = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_a_id = res_a.data['id']

        api_client.force_authenticate(user=patient_b)
        res_b = api_client.post('/api/v1/bookings/', {"slot": slot_b.id}, format='json')
        booking_b_id = res_b.data['id']

        # ClinicAdminA sees Centre A booking
        api_client.force_authenticate(user=clinic_admin_a)
        res_admin_a = api_client.get(f'/api/v1/bookings/{booking_a_id}/')
        assert res_admin_a.status_code == status.HTTP_200_OK

        # ClinicAdminA cannot see Centre B booking
        res_admin_b = api_client.get(f'/api/v1/bookings/{booking_b_id}/')
        assert res_admin_b.status_code == status.HTTP_404_NOT_FOUND

        # is_staff without membership gets no access to clinic bookings
        api_client.force_authenticate(user=staff_no_membership)
        res_staff = api_client.get(f'/api/v1/bookings/{booking_a_id}/')
        assert res_staff.status_code == status.HTTP_404_NOT_FOUND

        # Platform Admin sees all
        api_client.force_authenticate(user=platform_admin)
        res_super_a = api_client.get(f'/api/v1/bookings/{booking_a_id}/')
        res_super_b = api_client.get(f'/api/v1/bookings/{booking_b_id}/')
        assert res_super_a.status_code == status.HTTP_200_OK
        assert res_super_b.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestBookingCancellationAPI:

    # 35, 40, 41. Patient cancels own PENDING booking
    def test_patient_cancels_own_pending_booking(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code == status.HTTP_200_OK
        assert res_cancel.data['status'] == "CANCELLED"
        assert res_cancel.data['cancelled_at'] is not None

    # 37. patient cannot cancel another user's booking
    def test_patient_cannot_cancel_other_booking(self, api_client, patient_a, patient_b, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        api_client.force_authenticate(user=patient_b)
        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    # 38. CANCELLED booking cannot be cancelled again
    def test_cancelled_booking_cannot_be_cancelled_again(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        res_second_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_second_cancel.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSlotIntegrationAndCapacity:

    # 44, 45, 47, 48. Full slot hidden from patient slot list and available dates
    def test_full_slot_hidden_from_patient_and_available_dates(self, api_client, patient_a, patient_b, slot_a, centre_test_a):
        # Initial remaining capacity = 1
        api_client.force_authenticate(user=patient_a)
        res_slots = api_client.get(f'/api/v1/slots/?centre_test={centre_test_a.id}')
        assert res_slots.status_code == status.HTTP_200_OK
        results = res_slots.data['results'] if isinstance(res_slots.data, dict) and 'results' in res_slots.data else res_slots.data
        assert len(results) == 1
        assert results[0]['remaining_capacity'] == 1

        # Patient A books slot
        res_b = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res_b.data['id']

        # Patient B checks slots -> slot hidden because remaining_capacity = 0
        api_client.force_authenticate(user=patient_b)
        res_slots_b = api_client.get(f'/api/v1/slots/?centre_test={centre_test_a.id}')
        results_b = res_slots_b.data['results'] if isinstance(res_slots_b.data, dict) and 'results' in res_slots_b.data else res_slots_b.data
        assert len(results_b) == 0

        # Available dates is now empty
        res_dates = api_client.get(f'/api/v1/slots/available-dates/?centre_test={centre_test_a.id}')
        assert len(res_dates.data['dates']) == 0

        # Patient A cancels booking -> slot becomes available again
        api_client.force_authenticate(user=patient_a)
        api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')

        # Patient B checks slots again -> slot is visible again!
        api_client.force_authenticate(user=patient_b)
        res_slots_after = api_client.get(f'/api/v1/slots/?centre_test={centre_test_a.id}')
        results_after = res_slots_after.data['results'] if isinstance(res_slots_after.data, dict) and 'results' in res_slots_after.data else res_slots_after.data
        assert len(results_after) == 1
        assert results_after[0]['remaining_capacity'] == 1


@pytest.mark.django_db
class TestBookingEdgeCasesAndSecurity:

    def test_booking_inactive_diagnostic_test_rejected(self, api_client, patient_a, centre_a):
        inactive_test = DiagnosticTest.objects.create(name="Inactive Test", is_active=False)
        ct = CentreTest.objects.create(centre=centre_a, test=inactive_test, price=Decimal("400.00"), is_available=True)
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_booking_unavailable_centre_test_rejected(self, api_client, patient_a, centre_a, test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=test_1, price=Decimal("400.00"), is_available=False)
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_booking_past_slot_rejected(self, api_client, patient_a, centre_test_a):
        past_date = timezone.now().date() - datetime.timedelta(days=1)
        slot = AppointmentSlot.objects.create(centre_test=centre_test_a, date=past_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))

        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_booking_capacity_greater_than_1_multiple_users(self, api_client, patient_a, patient_b, centre_test_a):
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(centre_test=centre_test_a, date=future_date, start_time=datetime.time(11, 0), end_time=datetime.time(12, 0), capacity=2)

        # Patient A books
        api_client.force_authenticate(user=patient_a)
        res_a = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert res_a.status_code == status.HTTP_201_CREATED

        # Patient B books same slot (capacity 2)
        api_client.force_authenticate(user=patient_b)
        res_b = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert res_b.status_code == status.HTTP_201_CREATED

        # 3rd user booking attempt fails (409 Conflict)
        patient_c = User.objects.create_user(email="patientc@example.com", password="Password123!")
        api_client.force_authenticate(user=patient_c)
        res_c = api_client.post('/api/v1/bookings/', {"slot": slot.id}, format='json')
        assert res_c.status_code == status.HTTP_409_CONFLICT

    def test_booking_confirmed_booking_cancellation(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        # Transition booking to CONFIRMED
        booking = Booking.objects.get(id=booking_id)
        booking.status = Booking.Status.CONFIRMED
        booking.save()

        # Patient cancels CONFIRMED booking
        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code == status.HTTP_200_OK
        assert res_cancel.data['status'] == "CANCELLED"
        assert res_cancel.data['cancelled_at'] is not None

    def test_booking_failed_booking_cannot_cancel(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        booking = Booking.objects.get(id=booking_id)
        booking.status = Booking.Status.FAILED
        booking.save()

        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code == status.HTTP_400_BAD_REQUEST

    def test_booking_clinic_admin_cannot_cancel_patient_booking(self, api_client, patient_a, clinic_admin_a, centre_a, slot_a):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)

        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        # Clinic admin attempts to cancel patient's booking -> rejected
        api_client.force_authenticate(user=clinic_admin_a)
        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_booking_platform_admin_cancellation(self, api_client, patient_a, platform_admin, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        # Platform admin cancels booking
        api_client.force_authenticate(user=platform_admin)
        res_cancel = api_client.post(f'/api/v1/bookings/{booking_id}/cancel/')
        assert res_cancel.status_code == status.HTTP_200_OK
        assert res_cancel.data['status'] == "CANCELLED"

    def test_booking_patch_delete_methods_prohibited(self, api_client, patient_a, slot_a):
        api_client.force_authenticate(user=patient_a)
        res = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        booking_id = res.data['id']

        res_patch = api_client.patch(f'/api/v1/bookings/{booking_id}/', {"status": "CONFIRMED"}, format='json')
        assert res_patch.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        res_delete = api_client.delete(f'/api/v1/bookings/{booking_id}/')
        assert res_delete.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

