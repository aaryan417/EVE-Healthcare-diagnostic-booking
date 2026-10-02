from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
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
def diagnostic_test_2():
    return DiagnosticTest.objects.create(
        name="Lipid Profile",
        description="Lipid Test",
        is_active=True
    )


@pytest.fixture
def inactive_diagnostic_test():
    return DiagnosticTest.objects.create(
        name="Obsolete Test",
        description="Old Test",
        is_active=False
    )


    # 4. anonymous can GET diagnostic tests
    def test_anonymous_can_get_diagnostic_tests(self, api_client, diagnostic_test_1, diagnostic_test_2):
        response = api_client.get('/api/v1/tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        test_ids = [t['id'] for t in results]
        assert diagnostic_test_1.id in test_ids
        assert diagnostic_test_2.id in test_ids

    # 5. anonymous only sees active tests
    def test_anonymous_only_sees_active_tests(self, api_client, diagnostic_test_1, inactive_diagnostic_test):
        response = api_client.get('/api/v1/tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        test_ids = [t['id'] for t in results]
        assert diagnostic_test_1.id in test_ids
        assert inactive_diagnostic_test.id not in test_ids

    # 13. anonymous cannot POST diagnostic test
    def test_anonymous_cannot_post_diagnostic_test(self, api_client):
        payload = {"name": "Anon Global Test"}
        response = api_client.post('/api/v1/tests/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 14. anonymous cannot PATCH diagnostic test
    def test_anonymous_cannot_patch_diagnostic_test(self, api_client, diagnostic_test_1):
        payload = {"name": "Anon Updated Test"}
        response = api_client.patch(f'/api/v1/tests/{diagnostic_test_1.id}/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 9. patient can list active tests
    def test_patient_can_list_active_tests(self, api_client, patient_user, diagnostic_test_1, diagnostic_test_2):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        test_ids = [t['id'] for t in results]
        assert diagnostic_test_1.id in test_ids
        assert diagnostic_test_2.id in test_ids

    # 10. inactive test hidden from patient
    def test_inactive_test_hidden_from_patient(self, api_client, patient_user, diagnostic_test_1, inactive_diagnostic_test):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        test_ids = [t['id'] for t in results]
        assert diagnostic_test_1.id in test_ids
        assert inactive_diagnostic_test.id not in test_ids

    # 11. patient cannot create test
    def test_patient_cannot_create_test(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        payload = {"name": "Unauthorized Global Test"}
        response = api_client.post('/api/v1/tests/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 12. clinic admin cannot create global test
    def test_clinic_admin_cannot_create_global_test(self, api_client, clinic_admin_a):
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"name": "Clinic Admin Global Test"}
        response = api_client.post('/api/v1/tests/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 13. platform admin can create test
    def test_platform_admin_can_create_test(self, api_client, platform_admin):
        api_client.force_authenticate(user=platform_admin)
        payload = {"name": "Thyroid Profile", "description": "Measures T3, T4, TSH"}
        response = api_client.post('/api/v1/tests/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "Thyroid Profile"

    # 14. platform admin can update test
    def test_platform_admin_can_update_test(self, api_client, platform_admin, diagnostic_test_1):
        api_client.force_authenticate(user=platform_admin)
        payload = {"name": "Complete Blood Count (CBC)"}
        response = api_client.patch(f'/api/v1/tests/{diagnostic_test_1.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Complete Blood Count (CBC)"

    # 15. platform admin can deactivate test
    def test_platform_admin_can_deactivate_test(self, api_client, platform_admin, diagnostic_test_1):
        api_client.force_authenticate(user=platform_admin)
        payload = {"is_active": False}
        response = api_client.patch(f'/api/v1/tests/{diagnostic_test_1.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    # 16. platform admin can see inactive tests
    def test_platform_admin_can_see_inactive_tests(self, api_client, platform_admin, diagnostic_test_1, inactive_diagnostic_test):
        api_client.force_authenticate(user=platform_admin)
        response = api_client.get('/api/v1/tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        test_ids = [t['id'] for t in results]
        assert inactive_diagnostic_test.id in test_ids


@pytest.mark.django_db
class TestCentreTestReadAPI:

    # 6. anonymous can GET centre-tests
    def test_anonymous_can_get_centre_tests(self, api_client, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct.id in ct_ids

    # 7. anonymous only sees available offerings
    def test_anonymous_only_sees_available_offerings(self, api_client, centre_a, diagnostic_test_1, diagnostic_test_2, inactive_diagnostic_test):
        ct_avail = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        ct_unavail = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_2, price=Decimal("400.00"), is_available=False)
        ct_inactive_test = CentreTest.objects.create(centre=centre_a, test=inactive_diagnostic_test, price=Decimal("300.00"), is_available=True)

        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct_avail.id in ct_ids
        assert ct_unavail.id not in ct_ids
        assert ct_inactive_test.id not in ct_ids

    # 17. patient can list available CentreTests
    def test_patient_can_list_available_centre_tests(self, api_client, patient_user, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct.id in ct_ids

    # 18. patient can filter CentreTests by centre
    def test_patient_can_filter_centre_tests_by_centre(self, api_client, patient_user, centre_a, centre_b, diagnostic_test_1):
        ct_a = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        ct_b = CentreTest.objects.create(centre=centre_b, test=diagnostic_test_1, price=Decimal("650.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)

        response = api_client.get(f'/api/v1/centre-tests/?centre={centre_a.id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct_a.id in ct_ids
        assert ct_b.id not in ct_ids

    # 19. unavailable CentreTest hidden from patient
    def test_unavailable_centre_test_hidden_from_patient(self, api_client, patient_user, centre_a, diagnostic_test_1):
        ct_unavail = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=False)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct_unavail.id not in ct_ids

    # 20. inactive centre offering hidden from patient
    def test_inactive_centre_offering_hidden_from_patient(self, api_client, patient_user, diagnostic_test_1):
        inactive_c = DiagnosticCentre.objects.create(name="Inactive Lab", address="A", city="C", state="S", pincode="123", is_active=False)
        ct = CentreTest.objects.create(centre=inactive_c, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct.id not in ct_ids

    # 21. inactive DiagnosticTest offering hidden from patient
    def test_inactive_diagnostic_test_offering_hidden_from_patient(self, api_client, patient_user, centre_a, inactive_diagnostic_test):
        ct = CentreTest.objects.create(centre=centre_a, test=inactive_diagnostic_test, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centre-tests/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        ct_ids = [item['id'] for item in results]
        assert ct.id not in ct_ids

    # 22. nested centre/test information returned
    def test_nested_centre_test_information_returned(self, api_client, patient_user, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/centre-tests/{ct.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'centre' in response.data
        assert response.data['centre']['id'] == centre_a.id
        assert response.data['centre']['name'] == centre_a.name
        assert response.data['centre']['address'] == centre_a.address
        assert response.data['centre']['city'] == centre_a.city
        assert response.data['centre']['state'] == centre_a.state
        assert response.data['centre']['pincode'] == centre_a.pincode
        assert 'test' in response.data
        assert response.data['test']['id'] == diagnostic_test_1.id
        assert response.data['test']['name'] == diagnostic_test_1.name

    # 23. price serialized correctly
    def test_price_serialized_correctly(self, api_client, patient_user, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/centre-tests/{ct.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['price'] == "500.00"


@pytest.mark.django_db
class TestCentreTestWriteAPI:

    # 15. anonymous cannot POST centre-test
    def test_anonymous_cannot_post_centre_test(self, api_client, centre_a, diagnostic_test_1):
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "500.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 16. anonymous cannot PATCH centre-test
    def test_anonymous_cannot_patch_centre_test(self, api_client, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        payload = {"price": "600.00"}
        response = api_client.patch(f'/api/v1/centre-tests/{ct.id}/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 24. patient cannot create CentreTest
    def test_patient_cannot_create_centre_test(self, api_client, patient_user, centre_a, diagnostic_test_1):
        api_client.force_authenticate(user=patient_user)
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "500.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 25. patient cannot update CentreTest
    def test_patient_cannot_update_centre_test(self, api_client, patient_user, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=patient_user)
        payload = {"price": "600.00"}
        response = api_client.patch(f'/api/v1/centre-tests/{ct.id}/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 26. clinic admin can create offering for assigned centre
    def test_clinic_admin_can_create_offering_assigned_centre(self, api_client, clinic_admin_a, centre_a, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "550.00", "is_available": True}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['price'] == "550.00"

    # 27. clinic admin cannot create offering for unassigned centre
    def test_clinic_admin_cannot_create_offering_unassigned_centre(self, api_client, clinic_admin_a, centre_a, centre_b, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"centre": centre_b.id, "test": diagnostic_test_1.id, "price": "550.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 28. clinic admin can update assigned offering price
    def test_clinic_admin_can_update_assigned_offering_price(self, api_client, clinic_admin_a, centre_a, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"price": "575.00"}
        response = api_client.patch(f'/api/v1/centre-tests/{ct.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['price'] == "575.00"

    # 29. clinic admin can update assigned offering availability
    def test_clinic_admin_can_update_assigned_offering_availability(self, api_client, clinic_admin_a, centre_a, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"), is_available=True)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"is_available": False}
        response = api_client.patch(f'/api/v1/centre-tests/{ct.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_available'] is False

    # 30. clinic admin cannot update unassigned offering
    def test_clinic_admin_cannot_update_unassigned_offering(self, api_client, clinic_admin_a, centre_a, centre_b, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        ct_b = CentreTest.objects.create(centre=centre_b, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"price": "999.00"}
        response = api_client.patch(f'/api/v1/centre-tests/{ct_b.id}/', payload, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # 31. clinic admin cannot reassign centre
    def test_clinic_admin_cannot_reassign_centre(self, api_client, clinic_admin_a, centre_a, centre_b, diagnostic_test_1):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        ct_a = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"centre": centre_b.id}
        response = api_client.patch(f'/api/v1/centre-tests/{ct_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 32. clinic admin cannot replace test relationship
    def test_clinic_admin_cannot_replace_test_relationship(self, api_client, clinic_admin_a, centre_a, diagnostic_test_1, diagnostic_test_2):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        ct_a = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"test": diagnostic_test_2.id}
        response = api_client.patch(f'/api/v1/centre-tests/{ct_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 33. platform admin can create offering for any centre
    def test_platform_admin_can_create_offering_any_centre(self, api_client, platform_admin, centre_b, diagnostic_test_1):
        api_client.force_authenticate(user=platform_admin)
        payload = {"centre": centre_b.id, "test": diagnostic_test_1.id, "price": "700.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    # 34. platform admin can update any offering
    def test_platform_admin_can_update_any_offering(self, api_client, platform_admin, centre_a, diagnostic_test_1):
        ct = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=platform_admin)
        payload = {"price": "800.00"}
        response = api_client.patch(f'/api/v1/centre-tests/{ct.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK

    # 35. duplicate offering API request rejected
    def test_duplicate_offering_api_request_rejected(self, api_client, platform_admin, centre_a, diagnostic_test_1):
        CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        api_client.force_authenticate(user=platform_admin)
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "600.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 36. zero price API request rejected
    def test_zero_price_api_request_rejected(self, api_client, platform_admin, centre_a, diagnostic_test_1):
        api_client.force_authenticate(user=platform_admin)
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "0.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 37. negative price API request rejected
    def test_negative_price_api_request_rejected(self, api_client, platform_admin, centre_a, diagnostic_test_1):
        api_client.force_authenticate(user=platform_admin)
        payload = {"centre": centre_a.id, "test": diagnostic_test_1.id, "price": "-100.00"}
        response = api_client.post('/api/v1/centre-tests/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 38. MANDATORY TENANT ISOLATION TEST (Section 16)
    def test_section_16_mandatory_tenant_isolation(
        self, api_client, clinic_admin_a, centre_a, centre_b, diagnostic_test_1, diagnostic_test_2
    ):
        # Setup: ClinicAdminA -> Centre A
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)

        # CentreTestA -> Centre A, CentreTestB -> Centre B
        ct_a = CentreTest.objects.create(centre=centre_a, test=diagnostic_test_1, price=Decimal("500.00"))
        ct_b = CentreTest.objects.create(centre=centre_b, test=diagnostic_test_1, price=Decimal("600.00"))

        api_client.force_authenticate(user=clinic_admin_a)

        # 1) PATCH CentreTestA price => SUCCESS
        res1 = api_client.patch(f'/api/v1/centre-tests/{ct_a.id}/', {"price": "525.00"}, format='json')
        assert res1.status_code == status.HTTP_200_OK

        # 2) PATCH CentreTestB price => FAIL
        res2 = api_client.patch(f'/api/v1/centre-tests/{ct_b.id}/', {"price": "625.00"}, format='json')
        assert res2.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

        # 3) POST offering for Centre B => FAIL
        res3 = api_client.post('/api/v1/centre-tests/', {"centre": centre_b.id, "test": diagnostic_test_2.id, "price": "700.00"}, format='json')
        assert res3.status_code == status.HTTP_403_FORBIDDEN

        # 4) PATCH CentreTestA centre=CentreB => FAIL
        res4 = api_client.patch(f'/api/v1/centre-tests/{ct_a.id}/', {"centre": centre_b.id}, format='json')
        assert res4.status_code == status.HTTP_400_BAD_REQUEST
