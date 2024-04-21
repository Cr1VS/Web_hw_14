from unittest.mock import Mock
from typing import Any
import sys
import os

from sqlalchemy import select
import pytest


from tests.pytests.conf_test import postgresql_session
from src.entity.models import Consumer


# Add the project's root directory path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
user_data: dict[str, str] = {
    "username": "agent007",
    "email": "Vladislavovich@agent007.com",
    "password": "vlados",
}


def test_signup(client: Any, monkeypatch: Any) -> None:
    """Test signing up."""
    mock_send_email = Mock()
    monkeypatch.setattr("source.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data


def test_repeat_signup(client: Any, monkeypatch: Any) -> None:
    """Test repeating signup."""
    mock_send_email = Mock()
    monkeypatch.setattr("source.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


def test_not_confirmed_login(client: Any) -> None:
    """Test login with unconfirmed email."""
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(client: Any) -> None:
    """Test login."""
    async with postgresql_session() as session:
        current_user = await session.execute(
            select(Consumer).where(Consumer.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client: Any) -> None:
    """Test login with wrong password."""
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("email"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"
