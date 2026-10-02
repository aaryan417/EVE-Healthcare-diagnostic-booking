from decimal import Decimal
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)

User = get_user_model()


@pytest.mark.django_db
class TestDiagnosticModels:

    # 1. centre creation
    def test_centre_creation(self):
        centre = DiagnosticCentre.objects.create(
            name="Apollo Diagnostics",
            address="123 Health Ave",
            city="New Delhi",
            state="Delhi",
            pincode="110001"
        )
        assert centre.id is not None
        assert centre.name == "Apollo Diagnostics"
        assert centre.is_active is True

    # 2. centre string representation
    def test_centre_str(self):
        centre = DiagnosticCentre.objects.create(
            name="Max Lab",
            address="456 Care Road",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001"
        )
        assert str(centre) == "Max Lab"

    # 3. membership creation
    def test_membership_creation(self):
        user = User.objects.create_user(email="admin@clinic.com", password="Password123!", name="Clinic Admin")
        centre = DiagnosticCentre.objects.create(
            name="City Path",
            address="789 Main St",
            city="Bangalore",
            state="Karnataka",
            pincode="560001"
        )
        membership = CentreMembership.objects.create(
            user=user,
            centre=centre,
            role=CentreMembership.Role.ADMIN
        )
        assert membership.id is not None
        assert membership.user == user
        assert membership.centre == centre
        assert membership.role == CentreMembership.Role.ADMIN
        assert str(membership) == f"admin@clinic.com - City Path (ADMIN)"

    # 4. duplicate user-centre membership rejected
    def test_duplicate_membership_rejected(self):
        user = User.objects.create_user(email="user@clinic.com", password="Password123!", name="User")
        centre = DiagnosticCentre.objects.create(
            name="Diagnostic Hub",
            address="100 Lab St",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600001"
        )
        CentreMembership.objects.create(user=user, centre=centre, role=CentreMembership.Role.ADMIN)

        with pytest.raises(IntegrityError):
            CentreMembership.objects.create(user=user, centre=centre, role=CentreMembership.Role.ADMIN)

    # 5. membership role validation
    def test_membership_role_validation(self):
        user = User.objects.create_user(email="testrole@clinic.com", password="Password123!", name="User")
        centre = DiagnosticCentre.objects.create(
            name="Role Test Lab",
            address="101 Lab St",
            city="Pune",
            state="Maharashtra",
            pincode="411001"
        )
        membership = CentreMembership.objects.create(user=user, centre=centre, role="ADMIN")
        assert membership.role in CentreMembership.Role.values

    # Step 6 Model Tests

    # DiagnosticTest creation & str
    def test_diagnostic_test_creation(self):
        test = DiagnosticTest.objects.create(
            name="Complete Blood Count",
            description="Measures various blood components"
        )
        assert test.id is not None
        assert test.name == "Complete Blood Count"
        assert test.is_active is True
        assert str(test) == "Complete Blood Count"

    # CentreTest creation & str
    def test_centre_test_creation(self):
        centre = DiagnosticCentre.objects.create(
            name="Test Centre", address="Addr", city="City", state="State", pincode="123456"
        )
        test = DiagnosticTest.objects.create(name="Thyroid Profile")
        centre_test = CentreTest.objects.create(
            centre=centre,
            test=test,
            price=Decimal("450.00"),
            is_available=True
        )
        assert centre_test.id is not None
        assert centre_test.price == Decimal("450.00")
        assert str(centre_test) == f"{centre.name} - {test.name} (₹450.00)"

    def test_duplicate_centre_test_rejected(self):
        centre = DiagnosticCentre.objects.create(
            name="Dup Lab", address="Addr", city="City", state="State", pincode="123456"
        )
        test = DiagnosticTest.objects.create(name="HbA1c")
        CentreTest.objects.create(centre=centre, test=test, price=Decimal("500.00"))

        with pytest.raises(IntegrityError):
            CentreTest.objects.create(centre=centre, test=test, price=Decimal("600.00"))

    def test_zero_price_rejected(self):
        centre = DiagnosticCentre.objects.create(
            name="Zero Price Lab", address="Addr", city="City", state="State", pincode="123456"
        )
        test = DiagnosticTest.objects.create(name="Zero Test")
        ct = CentreTest(centre=centre, test=test, price=Decimal("0.00"))
        with pytest.raises(ValidationError):
            ct.full_clean()

    # Step 7 AppointmentSlot Model Tests

    @pytest.fixture
    def setup_ct(self):
        centre = DiagnosticCentre.objects.create(
            name="Slot Test Lab", address="Addr", city="City", state="State", pincode="123456"
        )
        test = DiagnosticTest.objects.create(name="Vitamin D Test")
        return CentreTest.objects.create(centre=centre, test=test, price=Decimal("1200.00"))

    # 1. slot creation succeeds
    def test_slot_creation_succeeds(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        slot = AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=2
        )
        assert slot.id is not None
        assert slot.capacity == 2

    # 2. slot string representation
    def test_slot_str(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        slot = AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )
        assert setup_ct.centre.name in str(slot)
        assert "09:00-10:00" in str(slot)

    # 3. capacity defaults to 1
    def test_capacity_defaults_to_1(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        slot = AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0)
        )
        assert slot.capacity == 1

    # 4. zero capacity rejected
    def test_zero_capacity_rejected(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        slot = AppointmentSlot(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=0
        )
        with pytest.raises(ValidationError):
            slot.full_clean()

    # 7. exact duplicate slot rejected
    def test_exact_duplicate_slot_rejected(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )
        with pytest.raises(IntegrityError):
            AppointmentSlot.objects.create(
                centre_test=setup_ct,
                date=future_date,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0)
            )

    # 9. adjacent slot accepted
    def test_adjacent_slot_accepted(self, setup_ct):
        future_date = timezone.now().date() + datetime.timedelta(days=2)
        s1 = AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )
        s2 = AppointmentSlot.objects.create(
            centre_test=setup_ct,
            date=future_date,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0)
        )
        assert s1.id is not None
        assert s2.id is not None

    # 10. same time different CentreTest accepted
    def test_same_time_different_centre_test_accepted(self):
        c1 = DiagnosticCentre.objects.create(name="Lab 1", address="A", city="C", state="S", pincode="123")
        c2 = DiagnosticCentre.objects.create(name="Lab 2", address="A", city="C", state="S", pincode="123")
        t = DiagnosticTest.objects.create(name="KFT")
        ct1 = CentreTest.objects.create(centre=c1, test=t, price=Decimal("300"))
        ct2 = CentreTest.objects.create(centre=c2, test=t, price=Decimal("350"))

        future_date = timezone.now().date() + datetime.timedelta(days=2)
        s1 = AppointmentSlot.objects.create(
            centre_test=ct1, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        s2 = AppointmentSlot.objects.create(
            centre_test=ct2, date=future_date, start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)
        )
        assert s1.id != s2.id
