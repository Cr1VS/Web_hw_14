from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from typing import Any


from fastapi.testclient import TestClient
import pytest


from src.services.auth import auth_service
from src.entity.models import User


@pytest.fixture()
def token(client: TestClient, user: dict[str, str], session: pytest.Session, monkeypatch: Any) -> str:
    """Fixture to get an access token."""
    mock_send_email = AsyncMock()
    monkeypatch.setattr("source.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    return data["access_token"]

def test_create_user(client: TestClient, token: str) -> None:
    """Test creating a user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.post(
            "/api/users",
            json={
                "first_name": "John",
                "second_name": "Doe",
                "email_add": "john.doe@example.com",
                "phone_num": "1234567890",
                "birth_date": datetime.now().date() - timedelta(days=1245),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["second_name"] == "Doe"
        assert "id" in data

def test_get_user(client: TestClient, token: str) -> None:
    """Test getting a user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/users/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["second_name"] == "Doe"
        assert "id" in data

def test_get_user_not_found(client: TestClient, token: str) -> None:
    """Test getting a non-existent user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/users/2", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "NOT FOUND"

def test_get_users(client: TestClient, token: str) -> None:
    """Test getting users."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == "John"
        assert "id" in data[0]

def test_update_user(client: TestClient, token: str) -> None:
    """Test updating a user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.put(
            "/api/users/1",
            json={
                "first_name": "Jane",
                "second_name": "Doe",
                "email_add": "jane.doe@example.com",
                "phone_num": "9876543210",
                "birth_date": datetime.now().date() - timedelta(days=124),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "Jane"
        assert "id" in data

def test_update_user_not_found(client: TestClient, token: str) -> None:
    """Test updating a non-existent user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.put(
            "/api/users/2",
            json={
                "first_name": "Jane",
                "second_name": "Doe",
                "email_add": "jane.doe@example.com",
                "phone_num": "9876543210",
                "birth_date": datetime.now().date() - timedelta(days=124),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "NOT FOUND"

def test_delete_user(client: TestClient, token: str) -> None:
    """Test deleting a user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.delete(
            "/api/users/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "Jane"
        assert "id" in data

def test_repeat_delete_user(client: TestClient, token: str) -> None:
    """Test deleting a non-existent user."""
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.delete(
            "/api/users/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "NOT FOUND"
        