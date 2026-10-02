import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def registered_user_data():
    return {
        "name": "Aaryan Verma",
        "email": "aaryan@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!"
    }


@pytest.fixture
def create_test_user():
    def _create_user(email="user@example.com", password="StrongPassword123!", name="Test User", is_active=True):
        return User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_active=is_active
        )
    return _create_user


@pytest.mark.django_db
class TestAuthenticationAPI:

    # 1. registration succeeds
    def test_registration_succeeds(self, api_client, registered_user_data):
        response = api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == registered_user_data['email']
        assert response.data['name'] == registered_user_data['name']
        assert 'id' in response.data
        assert 'password' not in response.data

    # 2. password stored hashed
    def test_password_stored_hashed(self, api_client, registered_user_data):
        api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        user = User.objects.get(email=registered_user_data['email'])
        assert user.check_password(registered_user_data['password']) is True
        assert user.password != registered_user_data['password']
        assert user.password.startswith('pbkdf2_argon2') or user.password.startswith('pbkdf2_sha256') or 'argon' in user.password or 'pbkdf2' in user.password

    # 3. duplicate email rejected
    def test_duplicate_email_rejected(self, api_client, registered_user_data):
        api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        # Attempt to register again with same email (case insensitive)
        duplicate_data = registered_user_data.copy()
        duplicate_data['email'] = registered_user_data['email'].upper()
        response = api_client.post('/api/v1/auth/register/', duplicate_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    # 4. password mismatch rejected
    def test_password_mismatch_rejected(self, api_client, registered_user_data):
        registered_user_data['password_confirm'] = "DifferentPassword123!"
        response = api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    # 5. weak password rejected
    def test_weak_password_rejected(self, api_client, registered_user_data):
        registered_user_data['password'] = "123"
        registered_user_data['password_confirm'] = "123"
        response = api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    # 6. missing required fields rejected
    def test_missing_required_fields_rejected(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert 'email' in response.data
        assert 'password' in response.data

    # 7. privilege escalation fields cannot create staff
    def test_privilege_escalation_cannot_create_staff(self, api_client, registered_user_data):
        registered_user_data['is_staff'] = True
        response = api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email=registered_user_data['email'])
        assert user.is_staff is False

    # 8. privilege escalation fields cannot create superuser
    def test_privilege_escalation_cannot_create_superuser(self, api_client, registered_user_data):
        registered_user_data['is_superuser'] = True
        response = api_client.post('/api/v1/auth/register/', registered_user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email=registered_user_data['email'])
        assert user.is_superuser is False

    # 9. login succeeds
    def test_login_succeeds(self, api_client, create_test_user):
        user = create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_200_OK

    # 10. login returns access token
    def test_login_returns_access_token(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert isinstance(response.data['access'], str)
        assert len(response.data['access']) > 0

    # 11. login returns refresh token
    def test_login_returns_refresh_token(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'refresh' in response.data
        assert isinstance(response.data['refresh'], str)
        assert len(response.data['refresh']) > 0

    # 12. wrong password rejected
    def test_wrong_password_rejected(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "WrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == "Invalid email or password."

    # 13. nonexistent email rejected generically
    def test_nonexistent_email_rejected_generically(self, api_client):
        login_data = {"email": "nonexistent@example.com", "password": "StrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == "Invalid email or password."

    # 14. inactive user cannot login
    def test_inactive_user_cannot_login(self, api_client, create_test_user):
        create_test_user(is_active=False)
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == "Invalid email or password."

    # 15. valid refresh token works
    def test_valid_refresh_token_works(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        login_response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        refresh_token = login_response.data['refresh']

        refresh_response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': refresh_token}, format='json')
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data

    # 16. invalid refresh token rejected
    def test_invalid_refresh_token_rejected(self, api_client):
        response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': 'invalid.jwt.token'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 17. anonymous /me rejected
    def test_anonymous_me_rejected(self, api_client):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 18. authenticated /me succeeds
    def test_authenticated_me_succeeds(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        login_response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        access_token = login_response.data['access']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK

    # 19. /me returns correct user
    def test_me_returns_correct_user(self, api_client, create_test_user):
        user = create_test_user(email="me@example.com", name="Me User")
        login_data = {"email": "me@example.com", "password": "StrongPassword123!"}
        login_response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        access_token = login_response.data['access']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id
        assert response.data['email'] == "me@example.com"
        assert response.data['name'] == "Me User"
        assert 'date_joined' in response.data

    # 20. /me does not expose password
    def test_me_does_not_expose_password(self, api_client, create_test_user):
        create_test_user()
        login_data = {"email": "user@example.com", "password": "StrongPassword123!"}
        login_response = api_client.post('/api/v1/auth/login/', login_data, format='json')
        access_token = login_response.data['access']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert 'password' not in response.data
        assert 'is_staff' not in response.data
        assert 'is_superuser' not in response.data
