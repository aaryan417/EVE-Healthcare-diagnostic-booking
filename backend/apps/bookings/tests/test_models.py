from decimal import Decimal
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.diagnostics.models import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)
from apps.bookings.models import Booking

User = get_user_model()


@pytest.mark.django_db
class TestBookingModels:

    @pytest.fixture
    def setup_entities(self):
        user = User.objects.create_user(email="patient@example.com", password="Password123!", name="Patient User")
        centre = DiagnosticCentre.objects.create(name="Lab A", address="Addr", city="City", state="State", pincode="123")
        test = DiagnosticTest.objects.create(name="Blood Test")
        ct = CentreTest.objects.create(centre=centre, test=test, price=Decimal("500.00"))
        future_date = timezone.now().date() + datetime.timedelta(days=3)
        slot = AppointmentSlot.objects.create(
            centre_test=ct, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), capacity=2
        )
        return user, ct, slot

    # 1. Booking creation & default status behavior
    def test_booking_creation_and_defaults(self, setup_entities):
        user, ct, slot = setup_entities
        booking = Booking.objects.create(
            user=user,
            centre_test=ct,
            slot=slot,
            amount=ct.price
        )
        assert booking.id is not None
        assert booking.status == Booking.Status.PENDING
        assert booking.cancelled_at is None
        assert booking.amount == Decimal("500.00")

    # 4. string representation
    def test_booking_str(self, setup_entities):
        user, ct, slot = setup_entities
        booking = Booking.objects.create(user=user, centre_test=ct, slot=slot, amount=ct.price)
        assert f"Booking #{booking.id}" in str(booking)
        assert "patient@example.com" in str(booking)

    # 5. centre_test/slot consistency validation
    def test_centre_test_slot_consistency_validation(self, setup_entities):
        user, ct1, slot1 = setup_entities
        centre2 = DiagnosticCentre.objects.create(name="Lab B", address="Addr", city="City", state="State", pincode="123")
        ct2 = CentreTest.objects.create(centre=centre2, test=ct1.test, price=Decimal("600.00"))

        booking = Booking(user=user, centre_test=ct2, slot=slot1, amount=Decimal("600.00"))
        with pytest.raises(ValidationError):
            booking.clean()

    # 7. conditional duplicate active booking protection
    def test_duplicate_active_booking_rejected(self, setup_entities):
        user, ct, slot = setup_entities
        Booking.objects.create(user=user, centre_test=ct, slot=slot, amount=ct.price, status=Booking.Status.PENDING)

        with pytest.raises(IntegrityError):
            Booking.objects.create(user=user, centre_test=ct, slot=slot, amount=ct.price, status=Booking.Status.PENDING)
