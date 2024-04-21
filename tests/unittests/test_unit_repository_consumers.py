from unittest.mock import AsyncMock, MagicMock
from typing import Optional
import unittest
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from src.repository.consumers import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar_url,
    update_password,
)
from sqlalchemy.ext.asyncio import AsyncSession


from src.schemas.consumer import UserSchema as C_schema
from src.entity.models import Consumer


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):
    """Unit tests for consumer-related functions."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.consumer = Consumer(
            id=1,
            username="Vlad",
            password="123123123",
            email="Vlad11134@google.com",
            refresh_token="old_token",
            confirmed=False,
            avatar="old_url.com.ua",
        )
        self.session: AsyncSession = AsyncMock(spec=AsyncSession)
        self.session.execute = AsyncMock()
        self.session.add = AsyncMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

    async def test_get_user_by_email(self) -> None:
        """Test retrieving a user by email."""
        email: str = "Vlad@Vladislavovich.com"
        self.session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=self.consumer))
        result: Optional[Consumer] = await get_user_by_email(email, self.session)
        self.assertEqual(result, self.consumer)

    async def test_create_user(self) -> None:
        """Test creating a new user."""
        body: C_schema = C_schema(
            username="Vlad",
            email="Vlad11134@google.com",
            password="123qwe123",
        )
        new_user: Consumer = await create_user(body, self.session)
        self.assertEqual(new_user.email, body.email)
        self.assertEqual(new_user.username, body.username)
        self.assertEqual(new_user.password, body.password)
        self.session.add.assert_awaited_once_with(new_user)
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(new_user)

    async def test_update_token(self) -> None:
        """Test updating a user's refresh token."""
        new_token: str = "new_token"
        await update_token(self.consumer, new_token, self.session)
        self.assertEqual(self.consumer.refresh_token, new_token)
        self.session.commit.assert_awaited_once()

    async def test_confirmed_email(self) -> None:
        """Test confirming a user's email."""
        self.session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=self.consumer))
        upd_user: Consumer = await confirmed_email(self.consumer.email, self.session)
        self.assertEqual(upd_user.confirmed, True)
        self.session.commit.assert_awaited_once()

    async def test_update_avatar_url(self) -> None:
        """Test updating a user's avatar URL."""
        url: str = "new_url.com.ua"
        upd_user: Consumer = await update_avatar_url(
            self.consumer.email, url, self.session
        )
        self.assertEqual(upd_user.avatar, url)
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(upd_user)

    async def test_update_password(self) -> None:
        """Test updating a user's password."""
        new_pass: str = "new_password"
        upd_user: Consumer = await update_password(
            self.consumer.email, new_pass, self.session
        )
        self.assertEqual(upd_user.password, new_pass)
        self.session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()