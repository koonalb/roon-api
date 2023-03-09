"""
Tests for heartbeat endpoint
"""
import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_anon_heartbeat(client):
    """
    Ensure the heartbeat url is accessible by anonymous users
    """
    url = reverse("heartbeat")
    result = client.get(url)

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == {'success': True}


@pytest.mark.django_db
def test_heartbeat_with_system_version(client):
    """
    Ensure the heartbeat url is accessible by anonymous users and able to get system_version
    """
    url = reverse("heartbeat")
    result = client.get(f"{url}?{'system_version=true'}")

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == {'success': True, 'system_version': settings.SYSTEM_VERSION}
