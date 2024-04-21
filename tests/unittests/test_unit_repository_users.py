from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import List, Optional
import unittest
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from sqlalchemy.ext.asyncio import AsyncSession


from src.repository.users import (
    get_users,
    get_all_users,
    get_users_by,
    get_user,
    get_users_birth,
    create_user,
    update_user,
    delete_user,
)
from src.entity.models import Consumer, User
from src.schemas.user import UserSchema


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):
    """Tests for async operations related to users."""

    async def asyncSetUp(self) -> None:
        """Set up async resources."""
        self.consumer: Consumer = Consumer(
            id=1, username="test_user", password="qwerty", confirmed=True
        )
        self.session: AsyncMock = AsyncMock(spec=AsyncSession)

    async def test_get_all_users(self) -> None:
        """Test fetching all users."""
        limit: int = 10
        offset: int = 0
        users: List[User] = [
            User(
                id=1,
                first_name="John",
                second_name="Doe",
                email_add="john.doe@example.com",
                phone_num="1234567890",
                birth_date="01-02-1988",
                consumer=self.consumer,
            ),
            User(
                id=2,
                first_name="Jane",
                second_name="Smith",
                email_add="jane.smith@example.com",
                phone_num="9876543210",
                birth_date="04-12-1990",
                consumer=self.consumer,
            ),
        ]
        mocked_users: MagicMock = MagicMock()
        mocked_users.scalars.return_value.all.return_value = users
        self.session.execute.return_value = mocked_users
        result: List[User] = await get_all_users(limit, offset, self.session, self.consumer)
        self.assertEqual(result, users)

    async def test_get_users(self) -> None:
        """Test fetching users."""
        limit: int = 10
        offset: int = 0
        users: List[User] = [
            User(
                id=1,
                first_name="John",
                second_name="Doe",
                email_add="john.doe@example.com",
                phone_num="1234567890",
                birth_date="01-02-1988",
                consumer=self.consumer,
            ),
            User(
                id=2,
                first_name="Jane",
                second_name="Smith",
                email_add="jane.smith@example.com",
                phone_num="9876543210",
                birth_date="04-12-1990",
                consumer=self.consumer,
            ),
        ]
        mocked_users: MagicMock = MagicMock()
        mocked_users.scalars.return_value.all.return_value = users
        self.session.execute.return_value = mocked_users
        result: List[User] = await get_users(limit, offset, self.session, self.consumer)
        self.assertEqual(result, users)

    async def test_create_user(self) -> None:
        """Test creating a user."""
        body: UserSchema = UserSchema(
            first_name="John",
            second_name="Doe",
            email_add="john.doe@example.com",
            phone_num="1234567890",
            birth_date=datetime.now().date() - timedelta(days=10000),
        )
        result: User = await create_user(body, self.session, self.consumer)
        self.assertIsInstance(result, User)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.email_add, body.email_add)

    async def test_update_user(self) -> None:
        """Test updating a user."""
        body: UserSchema = UserSchema(
            first_name="John",
            second_name="Doe",
            email_add="john.doe@example.com",
            phone_num="1234567890",
            birth_date=datetime.now().date() - timedelta(days=10000),
        )
        mocked_user: MagicMock = MagicMock()
        mocked_user.scalar_one_or_none.return_value = User(
            first_name="Valentin",
            second_name="Valentinovich",
            email_add="john.doe@example.com",
            phone_num="1234567890",
            birth_date=datetime.now().date() - timedelta(days=10000),
        )
        self.session.execute.return_value = mocked_user
        result: User = await update_user(1, body, self.session, self.consumer)
        self.assertIsInstance(result, User)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.birth_date, body.birth_date)

    async def test_delete_user(self) -> None:
        """Test deleting a user."""
        mocked_user: MagicMock = MagicMock()
        mocked_user.scalar_one_or_none.return_value = User(
            first_name="John",
            second_name="Doe",
            email_add="john.doe@example.com",
            phone_num="1234567890",
            birth_date=datetime.now().date() - timedelta(days=10000),
        )
        self.session.execute.return_value = mocked_user
        result: User = await delete_user(1, self.session, self.consumer)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, User)

    async def test_get_user(self) -> None:
        """Test fetching a user."""
        users: List[User] = [
            User(
                id=1,
                first_name="John",
                second_name="Doe",
                email_add="john.doe@example.com",
                phone_num="1234567890",
                birth_date="01-02-1988",
                consumer=self.consumer,
            ),
            User(
                id=2,
                first_name="Jane",
                second_name="Smith",
                email_add="jane.smith@example.com",
                phone_num="9876543210",
                birth_date="04-12-1990",
                consumer=self.consumer,
            ),
        ]
        mocked_users: MagicMock = MagicMock()
        mocked_users.scalar_one_or_none.return_value = users
        self.session.execute.return_value = mocked_users
        result: Optional[User] = await get_user(1, self.session, self.consumer)
        self.assertEqual(result, users)

    async def test_get_users_by(self) -> None:
        """Test fetching users by criteria."""
        users: List[User] = [
            User(
                id=1,
                first_name="John",
                second_name="Doe",
                email_add="john.doe@example.com",
                phone_num="1234567890",
                birth_date="01-02-1988",
                consumer=self.consumer,
            ),
            User(
                id=2,
                first_name="Jane",
                second_name="Smith",
                email_add="jane.smith@example.com",
                phone_num="9876543210",
                birth_date="04-12-1990",
                consumer=self.consumer,
            ),
        ]
        mocked_users: MagicMock = MagicMock()
        mocked_users.scalars.return_value.all.return_value = users
        self.session.execute.return_value = mocked_users
        result: List[User] = await get_users_by(
            "john", "doe", "john.doe@example.com", self.session, self.consumer
        )
        self.assertEqual(result[0].first_name, "John")
        self.assertEqual(result[1].first_name, "John")

    async def test_get_users_birth(self) -> None:
        """Test fetching users born after a given date."""
        limit: int = 2
        today: datetime.date = datetime.now().date()
        users: List[User] = [
            User(
                id=1,
                first_name="John",
                second_name="Doe",
                email_add="john.doe@example.com",
                phone_num="1234567890",
                birth_date=datetime.now().date() + timedelta(days=limit),
                consumer=self.consumer,
            ),
            User(
                id=2,
                first_name="Jane",
                second_name="Smith",
                email_add="jane.smith@example.com",
                phone_num="9876543210",
                birth_date=datetime.now().date() + timedelta(days=limit),
                consumer=self.consumer,
            ),
        ]
        mocked_users: MagicMock = MagicMock()
        mocked_users.scalars.return_value.all.return_value = users
        self.session.execute.return_value = mocked_users
        result: List[User] = await get_users_birth(limit, self.session, self.consumer)
        for user in result:
            self.assertGreater(user.birth_date, today)
