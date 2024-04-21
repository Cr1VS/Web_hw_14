from datetime import datetime, timedelta
from unittest.mock import patch
from typing import Any
import sys
import os


from fastapi.testclient import TestClient


# Add the project's root directory path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from src.services.auth import auth_service


def test_get_users(client: TestClient, get_token: str) -> None:
    """Test fetching users."""
    with patch.object(auth_service, "cache") as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("api/users", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 0

def test_create_user(client: TestClient, get_token: str, monkeypatch: Any) -> None:
    """Test creating a user."""
    with patch.object(auth_service, "cache") as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "api/users",
            headers=headers,
            json={
                "first_name": "vlad",
                "second_name": "sokov",
                "email_add": "vlad@google.com",
                "phone_num": "9876789878",
                "birth_date": datetime.now().date() + timedelta(days=1),
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data["second_name"] == "sokov"
        assert data["email_add"] == "vlad@google.com"
        