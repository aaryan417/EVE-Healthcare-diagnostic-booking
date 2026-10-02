import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.diagnostics.models import DiagnosticCentre, CentreMembership

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
def staff_user_no_membership():
    return User.objects.create_user(
        email="staff_no_member@clinic.com",
        password="Password123!",
        name="Staff User",
        is_staff=True
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
def inactive_centre():
    return DiagnosticCentre.objects.create(
        name="Inactive Centre",
        address="Inactive Address",
        city="City C",
        state="State C",
        pincode="100003",
        is_active=False
    )


@pytest.mark.django_db
class TestCentreAPI:

    # 1. anonymous can GET centre list
    def test_anonymous_can_get_centre_list(self, api_client, centre_a, centre_b):
        response = api_client.get('/api/v1/centres/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        centre_ids = [c['id'] for c in results]
        assert centre_a.id in centre_ids
        assert centre_b.id in centre_ids

    # 2. anonymous can GET centre detail
    def test_anonymous_can_get_centre_detail(self, api_client, centre_a):
        response = api_client.get(f'/api/v1/centres/{centre_a.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Centre A"

    # 3. anonymous only sees active centres
    def test_anonymous_only_sees_active_centres(self, api_client, centre_a, inactive_centre):
        response = api_client.get('/api/v1/centres/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        centre_ids = [c['id'] for c in results]
        assert centre_a.id in centre_ids
        assert inactive_centre.id not in centre_ids

    # 11. anonymous cannot POST centre
    def test_anonymous_cannot_post_centre(self, api_client):
        payload = {
            "name": "Anon Centre",
            "address": "123 St",
            "city": "City",
            "state": "State",
            "pincode": "123456"
        }
        response = api_client.post('/api/v1/centres/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 12. anonymous cannot PATCH centre
    def test_anonymous_cannot_patch_centre(self, api_client, centre_a):
        payload = {"name": "Anon Updated Name"}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 7. patient can list active centres
    def test_patient_can_list_active_centres(self, api_client, patient_user, centre_a, centre_b):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centres/')
        assert response.status_code == status.HTTP_200_OK
        centre_ids = [c['id'] for c in response.data['results'] if 'results' in response.data] if isinstance(response.data, dict) and 'results' in response.data else [c['id'] for c in response.data]
        assert centre_a.id in centre_ids
        assert centre_b.id in centre_ids

    # 8. inactive centre hidden from patient
    def test_inactive_centre_hidden_from_patient(self, api_client, patient_user, centre_a, inactive_centre):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/centres/')
        assert response.status_code == status.HTTP_200_OK
        centre_ids = [c['id'] for c in response.data['results']] if isinstance(response.data, dict) and 'results' in response.data else [c['id'] for c in response.data]
        assert centre_a.id in centre_ids
        assert inactive_centre.id not in centre_ids

    # 9. patient can retrieve active centre
    def test_patient_can_retrieve_active_centre(self, api_client, patient_user, centre_a):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get(f'/api/v1/centres/{centre_a.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Centre A"

    # 10. patient cannot create centre
    def test_patient_cannot_create_centre(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        payload = {
            "name": "Unauthorized Centre",
            "address": "123 St",
            "city": "City",
            "state": "State",
            "pincode": "123456"
        }
        response = api_client.post('/api/v1/centres/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 11. patient cannot update centre
    def test_patient_cannot_update_centre(self, api_client, patient_user, centre_a):
        api_client.force_authenticate(user=patient_user)
        payload = {"name": "Patient Updated Name"}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 12. platform admin can create centre
    def test_platform_admin_can_create_centre(self, api_client, platform_admin):
        api_client.force_authenticate(user=platform_admin)
        payload = {
            "name": "New Diagnostic Hub",
            "address": "456 Health Way",
            "city": "Gurgaon",
            "state": "Haryana",
            "pincode": "122001"
        }
        response = api_client.post('/api/v1/centres/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Diagnostic Hub"

    # 13. platform admin can update any centre
    def test_platform_admin_can_update_any_centre(self, api_client, platform_admin, centre_a):
        api_client.force_authenticate(user=platform_admin)
        payload = {"name": "Platform Admin Updated Name"}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Platform Admin Updated Name"

    # 14. platform admin can see inactive centres
    def test_platform_admin_can_see_inactive_centres(self, api_client, platform_admin, centre_a, inactive_centre):
        api_client.force_authenticate(user=platform_admin)
        response = api_client.get('/api/v1/centres/')
        assert response.status_code == status.HTTP_200_OK
        centre_ids = [c['id'] for c in response.data['results']] if isinstance(response.data, dict) and 'results' in response.data else [c['id'] for c in response.data]
        assert inactive_centre.id in centre_ids

    # 15. platform admin can deactivate centre
    def test_platform_admin_can_deactivate_centre(self, api_client, platform_admin, centre_a):
        api_client.force_authenticate(user=platform_admin)
        payload = {"is_active": False}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False


@pytest.mark.django_db
class TestClinicAdminSecurity:

    # 16. clinic admin can update assigned centre
    def test_clinic_admin_can_update_assigned_centre(self, api_client, clinic_admin_a, centre_a):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"name": "Clinic Admin A Updated Name"}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Clinic Admin A Updated Name"

    # 17. clinic admin cannot update unassigned centre
    def test_clinic_admin_cannot_update_unassigned_centre(self, api_client, clinic_admin_a, centre_a, centre_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"name": "Hacked Name"}
        response = api_client.patch(f'/api/v1/centres/{centre_b.id}/', payload, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # 18. changing URL ID cannot bypass centre authorization
    def test_changing_url_id_cannot_bypass_centre_auth(self, api_client, clinic_admin_a, centre_a, centre_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"address": "Illegal Address Edit"}
        response = api_client.patch(f'/api/v1/centres/{centre_b.id}/', payload, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # 19. is_staff user without membership cannot manage centre
    def test_is_staff_user_without_membership_cannot_manage_centre(self, api_client, staff_user_no_membership, centre_a):
        api_client.force_authenticate(user=staff_user_no_membership)
        payload = {"name": "Staff Attack"}
        response = api_client.patch(f'/api/v1/centres/{centre_a.id}/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 20. membership for Centre A gives no permission over Centre B
    def test_membership_centre_a_no_permission_centre_b(self, api_client, clinic_admin_a, centre_a, centre_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"city": "Malicious City"}
        response = api_client.patch(f'/api/v1/centres/{centre_b.id}/', payload, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # 15. SECTION 15 TENANT ISOLATION EXPLICIT TEST
    def test_section_15_tenant_isolation(self, api_client, clinic_admin_a, centre_a, centre_b):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)

        # PATCH /api/v1/centres/<centre-a-id>/ => succeeds
        res_a = api_client.patch(f'/api/v1/centres/{centre_a.id}/', {"name": "Valid Update A"}, format='json')
        assert res_a.status_code == status.HTTP_200_OK

        # PATCH /api/v1/centres/<centre-b-id>/ => must fail
        res_b = api_client.patch(f'/api/v1/centres/{centre_b.id}/', {"name": "Invalid Update B"}, format='json')
        assert res_b.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestMembershipAPI:

    # 21. platform admin can create membership
    def test_platform_admin_can_create_membership(self, api_client, platform_admin, patient_user, centre_a):
        api_client.force_authenticate(user=platform_admin)
        payload = {
            "user": patient_user.id,
            "centre": centre_a.id,
            "role": "ADMIN"
        }
        response = api_client.post('/api/v1/centre-memberships/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == patient_user.id
        assert response.data['centre'] == centre_a.id

    # 22. platform admin can list memberships
    def test_platform_admin_can_list_memberships(self, api_client, platform_admin, patient_user, centre_a):
        CentreMembership.objects.create(user=patient_user, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=platform_admin)
        response = api_client.get('/api/v1/centre-memberships/')
        assert response.status_code == status.HTTP_200_OK

    # 23. platform admin can delete membership
    def test_platform_admin_can_delete_membership(self, api_client, platform_admin, patient_user, centre_a):
        membership = CentreMembership.objects.create(user=patient_user, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=platform_admin)
        response = api_client.delete(f'/api/v1/centre-memberships/{membership.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CentreMembership.objects.filter(id=membership.id).exists()

    # 24. patient cannot create membership
    def test_patient_cannot_create_membership(self, api_client, patient_user, centre_a):
        api_client.force_authenticate(user=patient_user)
        payload = {"user": patient_user.id, "centre": centre_a.id, "role": "ADMIN"}
        response = api_client.post('/api/v1/centre-memberships/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 25. clinic admin cannot create membership
    def test_clinic_admin_cannot_create_membership(self, api_client, clinic_admin_a, patient_user, centre_a):
        CentreMembership.objects.create(user=clinic_admin_a, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=clinic_admin_a)
        payload = {"user": patient_user.id, "centre": centre_a.id, "role": "ADMIN"}
        response = api_client.post('/api/v1/centre-memberships/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 26. duplicate membership API request rejected
    def test_duplicate_membership_api_request_rejected(self, api_client, platform_admin, patient_user, centre_a):
        CentreMembership.objects.create(user=patient_user, centre=centre_a, role=CentreMembership.Role.ADMIN)
        api_client.force_authenticate(user=platform_admin)
        payload = {"user": patient_user.id, "centre": centre_a.id, "role": "ADMIN"}
        response = api_client.post('/api/v1/centre-memberships/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 27. invalid role rejected
    def test_invalid_role_rejected(self, api_client, platform_admin, patient_user, centre_a):
        api_client.force_authenticate(user=platform_admin)
        payload = {"user": patient_user.id, "centre": centre_a.id, "role": "SUPER_ADMIN"}
        response = api_client.post('/api/v1/centre-memberships/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
