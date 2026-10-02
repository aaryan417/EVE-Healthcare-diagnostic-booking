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
from django.db import IntegrityError
from apps.payments.models import Payment, WebhookEvent


@pytest.fixture
def pending_booking_and_payment(patient_a, centre_test_a, slot_a):
    booking = Booking.objects.create(
        user=patient_a,
        centre_test=centre_test_a,
        slot=slot_a,
        amount=centre_test_a.price,
        status=Booking.Status.PENDING
    )
    payment = Payment.objects.create(
        booking=booking,
        transaction_id="PAY_PENDING_TEST_001",
        amount=booking.amount,
        status=Payment.Status.PENDING
    )
    return booking, payment


@pytest.mark.django_db
class TestWebhookAPI:

    # 1. webhook works without JWT
    def test_webhook_works_without_jwt(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        api_client.credentials()  # Ensure unauthenticated
        payload = {
            "event_id": "evt_no_jwt_001",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == "success"

    # 2. missing event_id -> 400
    def test_webhook_missing_event_id(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 3. blank event_id -> 400
    def test_webhook_blank_event_id(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "   ",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 4. missing transaction_id -> 400
    def test_webhook_missing_transaction_id(self, api_client):
        payload = {
            "event_id": "evt_missing_tx",
            "event_type": "payment.updated",
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 5. invalid status -> 400
    def test_webhook_invalid_status(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_invalid_status",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "UNKNOWN"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 6. unknown transaction -> 404
    def test_webhook_unknown_transaction(self, api_client):
        payload = {
            "event_id": "evt_unknown_tx",
            "event_type": "payment.updated",
            "transaction_id": "PAY_NONEXISTENT_9999",
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert WebhookEvent.objects.filter(event_id="evt_unknown_tx").count() == 0

    # 7. PENDING Payment + SUCCESS -> Payment SUCCESS + Booking CONFIRMED
    def test_webhook_pending_payment_success(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_pending_success",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert booking.status == Booking.Status.CONFIRMED

    # 8. PENDING Payment + FAILED -> Payment FAILED + Booking FAILED
    def test_webhook_pending_payment_failed(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_pending_failed",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }
        res = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.FAILED
        assert booking.status == Booking.Status.FAILED

    # 9. duplicate event_id creates exactly ONE WebhookEvent
    def test_webhook_duplicate_event_creates_one_webhook_event(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_dup_single",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res1 = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res1.status_code == status.HTTP_200_OK
        res2 = api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data['status'] == "already_processed"
        assert WebhookEvent.objects.filter(event_id="evt_dup_single").count() == 1

    # 10. duplicate event does not create another Payment
    def test_webhook_duplicate_event_does_not_create_another_payment(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        initial_payment_count = Payment.objects.count()
        payload = {
            "event_id": "evt_dup_pay_count",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert Payment.objects.count() == initial_payment_count

    # 11. duplicate event does not create another Booking
    def test_webhook_duplicate_event_does_not_create_another_booking(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        initial_booking_count = Booking.objects.count()
        payload = {
            "event_id": "evt_dup_book_count",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        assert Booking.objects.count() == initial_booking_count

    # 12. duplicate event does not modify Payment twice
    def test_webhook_duplicate_event_does_not_modify_payment_twice(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_dup_mod_pay",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        payment.refresh_from_db()
        updated_at_1 = payment.updated_at

        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        payment.refresh_from_db()
        assert payment.updated_at == updated_at_1

    # 13. duplicate event does not modify Booking twice
    def test_webhook_duplicate_event_does_not_modify_booking_twice(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload = {
            "event_id": "evt_dup_mod_book",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        booking.refresh_from_db()
        updated_at_1 = booking.updated_at

        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        booking.refresh_from_db()
        assert booking.updated_at == updated_at_1

    # 14. SUCCESS -> conflicting FAILED webhook rejected
    def test_webhook_success_conflicting_failed_rejected(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        # First succeed
        api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_success_init",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }, format='json')

        # Now send conflicting FAILED with a NEW event_id
        res = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_failed_conflict",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert booking.status == Booking.Status.CONFIRMED

    # 15. FAILED -> conflicting SUCCESS webhook rejected
    def test_webhook_failed_conflicting_success_rejected(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        # First fail
        api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_fail_init",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }, format='json')

        # Now send conflicting SUCCESS with a NEW event_id
        res = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_success_conflict",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.FAILED
        assert booking.status == Booking.Status.FAILED

    # 16. CANCELLED booking cannot be revived
    def test_webhook_cancelled_booking_cannot_be_revived(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        booking.status = Booking.Status.CANCELLED
        booking.save()

        res = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_revive_cancelled",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CANCELLED

    # 17. consistent SUCCESS terminal replay safe
    def test_webhook_consistent_success_replay_safe(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        # First SUCCESS
        api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_succ_1",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }, format='json')

        # Second SUCCESS with different event_id
        res = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_succ_2",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert booking.status == Booking.Status.CONFIRMED

    # 18. consistent FAILED terminal replay safe
    def test_webhook_consistent_failed_replay_safe(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        # First FAILED
        api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_fail_1",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }, format='json')

        # Second FAILED with different event_id
        res = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_fail_2",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.FAILED
        assert booking.status == Booking.Status.FAILED

    # 19. database directly rejects duplicate event_id
    def test_webhook_db_rejects_duplicate_event_id(self):
        WebhookEvent.objects.create(
            event_id="evt_db_dup_101",
            event_type="payment.updated",
            transaction_id="PAY_101"
        )
        with pytest.raises(IntegrityError):
            WebhookEvent.objects.create(
                event_id="evt_db_dup_101",
                event_type="payment.updated",
                transaction_id="PAY_101"
            )

    # 20. FAILED webhook releases slot capacity
    def test_webhook_failed_releases_capacity(self, api_client, patient_a, patient_b, centre_test_a, slot_a):
        booking_a = Booking.objects.create(
            user=patient_a, centre_test=centre_test_a, slot=slot_a, amount=centre_test_a.price, status=Booking.Status.PENDING
        )
        payment_a = Payment.objects.create(
            booking=booking_a, transaction_id="PAY_CAP_001", amount=booking_a.amount, status=Payment.Status.PENDING
        )

        api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_cap_release",
            "event_type": "payment.updated",
            "transaction_id": payment_a.transaction_id,
            "status": "FAILED"
        }, format='json')

        api_client.force_authenticate(user=patient_b)
        res_book_b = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res_book_b.status_code == status.HTTP_201_CREATED

    # 21. SUCCESS webhook keeps capacity consumed
    def test_webhook_success_keeps_capacity_consumed(self, api_client, patient_a, patient_b, centre_test_a, slot_a):
        api_client.credentials()
        booking_a = Booking.objects.create(
            user=patient_a, centre_test=centre_test_a, slot=slot_a, amount=centre_test_a.price, status=Booking.Status.PENDING
        )
        payment_a = Payment.objects.create(
            booking=booking_a, transaction_id="PAY_CAP_002", amount=booking_a.amount, status=Payment.Status.PENDING
        )

        res_wh = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_cap_consumed",
            "event_type": "payment.updated",
            "transaction_id": payment_a.transaction_id,
            "status": "SUCCESS"
        }, format='json')
        assert res_wh.status_code == status.HTTP_200_OK

        api_client.force_authenticate(user=patient_b)
        res_book_b = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res_book_b.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]


    # 22. duplicate webhook leaves capacity unchanged
    def test_webhook_duplicate_leaves_capacity_unchanged(self, api_client, pending_booking_and_payment, slot_a):
        booking, payment = pending_booking_and_payment
        def get_rem_cap():
            active_count = slot_a.bookings.filter(status__in=['PENDING', 'CONFIRMED']).count()
            return max(0, slot_a.capacity - active_count)

        payload = {
            "event_id": "evt_cap_dup",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        cap_after_1 = get_rem_cap()

        api_client.post('/api/v1/payments/webhook/', payload, format='json')
        cap_after_2 = get_rem_cap()

        assert cap_after_1 == cap_after_2

    # 23. same event_id with contradictory payload cannot apply second payload
    def test_webhook_contradictory_second_payload_ignored(self, api_client, pending_booking_and_payment):
        booking, payment = pending_booking_and_payment
        payload_1 = {
            "event_id": "evt_contradict_100",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "FAILED"
        }
        api_client.post('/api/v1/payments/webhook/', payload_1, format='json')
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.FAILED
        assert booking.status == Booking.Status.FAILED

        payload_2 = {
            "event_id": "evt_contradict_100",
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }
        res2 = api_client.post('/api/v1/payments/webhook/', payload_2, format='json')
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data['status'] == "already_processed"

        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.FAILED
        assert booking.status == Booking.Status.FAILED

    # 24. cross-transaction idempotency remains correct
    def test_webhook_cross_transaction_idempotency(self, api_client, patient_a, patient_b, centre_test_a, centre_test_b, slot_a):
        b1 = Booking.objects.create(user=patient_a, centre_test=centre_test_a, slot=slot_a, amount=Decimal("500.00"), status=Booking.Status.PENDING)
        p1 = Payment.objects.create(booking=b1, transaction_id="PAY_CROSS_1", amount=b1.amount, status=Payment.Status.PENDING)

        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot_b = AppointmentSlot.objects.create(centre_test=centre_test_b, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        b2 = Booking.objects.create(user=patient_b, centre_test=centre_test_b, slot=slot_b, amount=Decimal("600.00"), status=Booking.Status.PENDING)
        p2 = Payment.objects.create(booking=b2, transaction_id="PAY_CROSS_2", amount=b2.amount, status=Payment.Status.PENDING)

        res1 = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_cross_1",
            "event_type": "payment.updated",
            "transaction_id": p1.transaction_id,
            "status": "SUCCESS"
        }, format='json')
        assert res1.status_code == status.HTTP_200_OK

        res2 = api_client.post('/api/v1/payments/webhook/', {
            "event_id": "evt_cross_2",
            "event_type": "payment.updated",
            "transaction_id": p2.transaction_id,
            "status": "FAILED"
        }, format='json')
        assert res2.status_code == status.HTTP_200_OK

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.status == Payment.Status.SUCCESS
        assert p2.status == Payment.Status.FAILED

    # 25. concurrency race condition safety test
    @pytest.mark.django_db(transaction=True)
    def test_webhook_concurrency_race_condition_safe(self, patient_a, centre_test_a, slot_a):
        import concurrent.futures
        from django.db import connections
        from apps.payments.services import process_payment_webhook

        booking = Booking.objects.create(
            user=patient_a,
            centre_test=centre_test_a,
            slot=slot_a,
            amount=centre_test_a.price,
            status=Booking.Status.PENDING
        )
        payment = Payment.objects.create(
            booking=booking,
            transaction_id="PAY_RACE_TEST_999",
            amount=booking.amount,
            status=Payment.Status.PENDING
        )
        event_id = "evt_race_condition_test_999"
        payload = {
            "event_id": event_id,
            "event_type": "payment.updated",
            "transaction_id": payment.transaction_id,
            "status": "SUCCESS"
        }

        def worker():
            connections.close_all()
            return process_payment_webhook(
                event_id=event_id,
                event_type="payment.updated",
                transaction_id=payment.transaction_id,
                status_str="SUCCESS",
                payload=payload
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(worker)
            f2 = executor.submit(worker)
            r1 = f1.result()
            r2 = f2.result()

        connections.close_all()
        assert WebhookEvent.objects.filter(event_id=event_id).count() == 1

        statuses = [r1['status'], r2['status']]
        assert "success" in statuses
        assert "already_processed" in statuses

        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert booking.status == Booking.Status.CONFIRMED



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
        email="staff_no_member@clinic.com", password="Password123!", name="Staff User", is_staff=True
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
    return DiagnosticTest.objects.create(name="Blood Profile", is_active=True)


@pytest.fixture
def centre_test_a(centre_a, test_1):
    return CentreTest.objects.create(centre=centre_a, test=test_1, price=Decimal("500.00"), is_available=True)


@pytest.fixture
def centre_test_b(centre_b, test_1):
    return CentreTest.objects.create(centre=centre_b, test=test_1, price=Decimal("600.00"), is_available=True)


@pytest.fixture
def slot_a(centre_test_a):
    future_date = timezone.now().date() + datetime.timedelta(days=3)
    return AppointmentSlot.objects.create(
        centre_test=centre_test_a, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), capacity=1
    )


@pytest.fixture
def booking_a(patient_a, centre_test_a, slot_a):
    return Booking.objects.create(
        user=patient_a,
        centre_test=centre_test_a,
        slot=slot_a,
        amount=centre_test_a.price,
        status=Booking.Status.PENDING
    )


@pytest.mark.django_db
class TestPaymentAPI:

    # 7. anonymous payment rejected
    def test_anonymous_payment_rejected(self, api_client, booking_a):
        response = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 8, 9, 10. SUCCESS payment transitions PENDING -> CONFIRMED
    def test_patient_can_pay_own_booking_success(self, api_client, patient_a, booking_a):
        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == "SUCCESS"
        assert response.data['booking_status'] == "CONFIRMED"
        assert response.data['amount'] == "500.00"
        assert response.data['transaction_id'].startswith("PAY_")

        booking_a.refresh_from_db()
        assert booking_a.status == Booking.Status.CONFIRMED

    # 11, 12. FAILED payment transitions PENDING -> FAILED
    def test_patient_can_pay_own_booking_failed(self, api_client, patient_a, booking_a):
        api_client.force_authenticate(user=patient_a)
        response = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "FAILED"}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == "FAILED"
        assert response.data['booking_status'] == "FAILED"

        booking_a.refresh_from_db()
        assert booking_a.status == Booking.Status.FAILED

    # 13, 14, 15, 16, 17. Amount snapshot integrity & client input bounds
    def test_payment_amount_integrity(self, api_client, patient_a, booking_a, centre_test_a):
        assert booking_a.amount == Decimal("500.00")

        # CentreTest price changes to 700.00
        centre_test_a.price = Decimal("700.00")
        centre_test_a.save()

        # Client attempts to pass amount=100.00, transaction_id="HACK", status="FAILED"
        api_client.force_authenticate(user=patient_a)
        payload = {
            "booking": booking_a.id,
            "simulate_result": "SUCCESS",
            "amount": "100.00",
            "transaction_id": "HACK_TX",
            "status": "FAILED"
        }
        response = api_client.post('/api/v1/payments/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == "500.00"  # EQUALS booking.amount = 500.00
        assert response.data['status'] == "SUCCESS"
        assert response.data['transaction_id'] != "HACK_TX"

    # 18. Patient A cannot pay Patient B booking
    def test_patient_a_cannot_pay_patient_b_booking(self, api_client, patient_b, booking_a):
        api_client.force_authenticate(user=patient_b)
        response = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 19. clinic admin cannot initiate patient payment
    def test_clinic_admin_cannot_initiate_payment(self, api_client, clinic_admin_a, centre_a, booking_a):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        response = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 20, 21, 22, 23. Cannot pay non-PENDING booking / Second payment attempt rejected
    def test_second_payment_attempt_rejected(self, api_client, patient_a, booking_a):
        api_client.force_authenticate(user=patient_a)
        res1 = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert res1.status_code == status.HTTP_201_CREATED

        res2 = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    # 24, 25, 26. Failed payment releases capacity; another user can book
    def test_failed_payment_releases_capacity_for_rebooking(self, api_client, patient_a, patient_b, booking_a, slot_a):
        # Slot capacity is 1. Booking A is PENDING.
        api_client.force_authenticate(user=patient_a)

        # Payment FAILED for Booking A -> transitions Booking A to FAILED
        res_fail = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "FAILED"}, format='json')
        assert res_fail.status_code == status.HTTP_201_CREATED

        # Patient B attempts booking same slot -> succeeds because capacity is released!
        api_client.force_authenticate(user=patient_b)
        res_book_b = api_client.post('/api/v1/bookings/', {"slot": slot_a.id}, format='json')
        assert res_book_b.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestPaymentVisibilityAndSecurity:

    # 27, 28, 29. Patient visibility isolation
    def test_patient_payment_visibility_isolation(self, api_client, patient_a, patient_b, booking_a, slot_a, centre_test_b):
        # Patient A pays Booking A
        api_client.force_authenticate(user=patient_a)
        res_a = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        payment_a_id = res_a.data['id']

        # Patient B creates and pays Booking B
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot_b = AppointmentSlot.objects.create(centre_test=centre_test_b, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        booking_b = Booking.objects.create(user=patient_b, centre_test=centre_test_b, slot=slot_b, amount=centre_test_b.price)

        api_client.force_authenticate(user=patient_b)
        res_b = api_client.post('/api/v1/payments/', {"booking": booking_b.id, "simulate_result": "SUCCESS"}, format='json')
        payment_b_id = res_b.data['id']

        # Patient A lists payments -> sees only Payment A
        api_client.force_authenticate(user=patient_a)
        res_list = api_client.get('/api/v1/payments/')
        results = res_list.data['results'] if isinstance(res_list.data, dict) and 'results' in res_list.data else res_list.data
        p_ids = [p['id'] for p in results]
        assert payment_a_id in p_ids
        assert payment_b_id not in p_ids

        # Patient A cannot retrieve Payment B (404)
        res_get = api_client.get(f'/api/v1/payments/{payment_b_id}/')
        assert res_get.status_code == status.HTTP_404_NOT_FOUND

    # 30, 31, 32, 33. Clinic Admin and Platform Admin visibility
    def test_clinic_admin_and_platform_admin_payment_visibility(
        self, api_client, patient_a, clinic_admin_a, staff_no_membership, platform_admin, centre_a, booking_a
    ):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)

        api_client.force_authenticate(user=patient_a)
        res_p = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        payment_id = res_p.data['id']

        # ClinicAdmin A can view Payment A
        api_client.force_authenticate(user=clinic_admin_a)
        res_admin = api_client.get(f'/api/v1/payments/{payment_id}/')
        assert res_admin.status_code == status.HTTP_200_OK

        # Staff with no membership gets 404
        api_client.force_authenticate(user=staff_no_membership)
        res_staff = api_client.get(f'/api/v1/payments/{payment_id}/')
        assert res_staff.status_code == status.HTTP_404_NOT_FOUND

        # Platform admin gets 200
        api_client.force_authenticate(user=platform_admin)
        res_super = api_client.get(f'/api/v1/payments/{payment_id}/')
        assert res_super.status_code == status.HTTP_200_OK

    def test_payment_put_patch_delete_prohibited(self, api_client, patient_a, booking_a):
        api_client.force_authenticate(user=patient_a)
        res_p = api_client.post('/api/v1/payments/', {"booking": booking_a.id, "simulate_result": "SUCCESS"}, format='json')
        payment_id = res_p.data['id']

        res_put = api_client.put(f'/api/v1/payments/{payment_id}/', {"status": "FAILED"}, format='json')
        assert res_put.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        res_patch = api_client.patch(f'/api/v1/payments/{payment_id}/', {"status": "FAILED"}, format='json')
        assert res_patch.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        res_delete = api_client.delete(f'/api/v1/payments/{payment_id}/')
        assert res_delete.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


