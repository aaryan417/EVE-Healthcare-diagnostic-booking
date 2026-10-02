from decimal import Decimal
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.diagnostics.models import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)
from apps.bookings.models import Booking
from apps.payments.models import Payment

User = get_user_model()


@pytest.mark.django_db
class TestPaymentModels:

    @pytest.fixture
    def setup_booking(self):
        user = User.objects.create_user(email="patient@example.com", password="Password123!", name="Patient User")
        centre = DiagnosticCentre.objects.create(name="Lab A", address="Addr", city="City", state="State", pincode="123")
        test = DiagnosticTest.objects.create(name="Blood Test")
        ct = CentreTest.objects.create(centre=centre, test=test, price=Decimal("500.00"))
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(
            centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        booking = Booking.objects.create(user=user, centre_test=ct, slot=slot, amount=ct.price)
        return booking

    # 1. Payment creation & 3. Decimal amount
    def test_payment_creation(self, setup_booking):
        payment = Payment.objects.create(
            booking=setup_booking,
            transaction_id="PAY_TEST123",
            amount=setup_booking.amount,
            status=Payment.Status.SUCCESS
        )
        assert payment.id is not None
        assert payment.transaction_id == "PAY_TEST123"
        assert payment.amount == Decimal("500.00")
        assert payment.status == Payment.Status.SUCCESS

    # 2. transaction_id uniqueness
    def test_transaction_id_uniqueness(self, setup_booking):
        Payment.objects.create(
            booking=setup_booking,
            transaction_id="PAY_UNIQUE_123",
            amount=setup_booking.amount
        )
        with pytest.raises(IntegrityError):
            Payment.objects.create(
                booking=setup_booking,
                transaction_id="PAY_UNIQUE_123",
                amount=setup_booking.amount
            )

    # 4. Payment string representation
    def test_payment_str(self, setup_booking):
        payment = Payment.objects.create(
            booking=setup_booking,
            transaction_id="PAY_STR_TEST",
            amount=setup_booking.amount
        )
        assert f"Payment #{payment.id}" in str(payment)
        assert "PAY_STR_TEST" in str(payment)
