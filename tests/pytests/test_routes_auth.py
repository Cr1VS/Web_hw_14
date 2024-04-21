from unittest.mock import AsyncMock
from pytest import Session
from typing import Any


from fastapi.testclient import TestClient
from src.entity.models import Consumer


def test_create_user(client: TestClient, user: dict[str, str], monkeypatch: Any) -> None:
    """Test creating a user."""
    mock_send_email = AsyncMock()
    monkeypatch.setattr("source.routes.auth.send_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]

def test_repeat_create_user(client: TestClient, user: dict[str, str]) -> None:
    """Test repeating creating a user."""
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"

def test_login_user_not_confirmed(client: TestClient, user: dict[str, str]) -> None:
    """Test login with unconfirmed email."""
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"

def test_login_user(client: TestClient, session: Session, user: dict[str, str]) -> None:
    """Test login."""
    current_user: Consumer = (
        session.query(Consumer).filter(Consumer.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, user: dict[str, str]) -> None:
    """Test login with wrong password."""
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"

def test_login_wrong_email(client: TestClient, user: dict[str, str]) -> None:
    """Test login with wrong email."""
    response = client.post(
        "/api/auth/login",
        data={"username": "email", "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"
    