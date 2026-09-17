import pytest
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
def test_health_endpoint():
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "medicare-api"
    assert data["database"]["status"] == "connected"
    assert data["database"]["vendor"] == "postgresql"
