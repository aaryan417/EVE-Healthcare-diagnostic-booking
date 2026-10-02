import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.diagnostics.models import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
    CentreMembership,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()



@pytest.mark.django_db
class TestSeedDemoCommand:

    def test_seed_demo_executes_successfully_and_creates_data(self):
        call_command('seed_demo')

        # Verify users created
        assert User.objects.filter(email='admin@evehealthcare.com', is_superuser=True, is_staff=True).exists()
        assert User.objects.filter(email='centreadmin_a@clinic.com', is_staff=False).exists()
        assert User.objects.filter(email='patient@example.com', is_staff=False).exists()

        # Verify membership
        admin_a = User.objects.get(email='centreadmin_a@clinic.com')
        assert CentreMembership.objects.filter(user=admin_a, role=CentreMembership.Role.ADMIN).exists()

        # Verify domain data
        assert DiagnosticCentre.objects.count() >= 3
        assert DiagnosticTest.objects.count() >= 12
        assert CentreTest.objects.count() >= 31
        assert AppointmentSlot.objects.count() > 0


    def test_seed_demo_is_idempotent(self):
        # Run 1st time
        call_command('seed_demo')
        user_count_1 = User.objects.count()
        centre_count_1 = DiagnosticCentre.objects.count()
        test_count_1 = DiagnosticTest.objects.count()
        ct_count_1 = CentreTest.objects.count()
        slot_count_1 = AppointmentSlot.objects.count()

        # Run 2nd time
        call_command('seed_demo')
        assert User.objects.count() == user_count_1
        assert DiagnosticCentre.objects.count() == centre_count_1
        assert DiagnosticTest.objects.count() == test_count_1
        assert CentreTest.objects.count() == ct_count_1
        assert AppointmentSlot.objects.count() == slot_count_1

    def test_demo_accounts_authentication(self, api_client):
        call_command('seed_demo')

        # Patient authentication
        res_patient = api_client.post('/api/v1/auth/login/', {
            'email': 'patient@example.com',
            'password': 'PatientPass123!'
        }, format='json')
        assert res_patient.status_code == 200
        assert 'access' in res_patient.data

        # Centre Admin authentication & me endpoint
        res_admin = api_client.post('/api/v1/auth/login/', {
            'email': 'centreadmin_a@clinic.com',
            'password': 'AdminPass123!'
        }, format='json')
        assert res_admin.status_code == 200
        token = res_admin.data['access']


        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res_me = api_client.get('/api/v1/centre-admin/me/')
        assert res_me.status_code == 200
        assert res_me.data['is_centre_admin'] is True
        assert len(res_me.data['centres']) > 0
