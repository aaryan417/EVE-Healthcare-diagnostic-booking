import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestCoreEndpoints:

    def test_health_check_returns_200_without_auth(self, api_client):
        response = api_client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        assert response.data['database'] == 'ok'

    def test_openapi_schema_endpoint_works(self, api_client):
        response = api_client.get('/api/schema/')
        assert response.status_code == status.HTTP_200_OK
        content_type = response['Content-Type'].lower()
        assert 'openapi' in content_type or 'json' in content_type or 'yaml' in content_type


    def test_openapi_swagger_ui_endpoint_works(self, api_client):
        response = api_client.get('/api/docs/')
        assert response.status_code == status.HTTP_200_OK
        assert 'text/html' in response['Content-Type']
