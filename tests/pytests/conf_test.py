import pytest_asyncio
import pytest
import sys
import os

# Add the project's root directory path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import necessary modules for database and application
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Import models and services
from src.entity.models import Base, Consumer
from src.services.auth import auth_service
from src.database.db import get_db
from main import app


# Define test user data
test_user = {"username": "John", "email": "John123@foks.com", "password": "qwe123123"}

# Define the URL to connect to the PostgreSQL database
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://user:password@localhost/test_db"


# Fixture for PostgreSQL session creation
@pytest.fixture(scope="session")
def postgresql_session() -> sessionmaker: # type: ignore
    """Fixture to create a SQLAlchemy session for the PostgreSQL database."""
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    yield Session
    Base.metadata.drop_all(engine)


# Fixture to initialize models in the database
@pytest.fixture(scope="module", autouse=True)
async def init_models_wrap(postgresql_session: sessionmaker):
    """Fixture to initialize models in the database before tests."""
    async with postgresql_session() as session:
        async with Engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSession(bind=Engine) as session:
            hash_password = auth_service.get_password_hash(test_user["password"])
            current_user = Consumer(
                username=test_user["username"],
                email=test_user["email"],
                password=hash_password,
                confirmed=True,
                role="admin",
            )
            session.add(current_user)
            await session.commit()


# Fixture to create a TestClient for the application
@pytest.fixture(scope="module")
def client() -> TestClient: # type: ignore
    """Fixture to create a TestClient for testing the FastAPI application."""

    async def override_get_db() -> AsyncSession: # type: ignore
        session = AsyncSession()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


# Fixture to get an access token for testing
@pytest_asyncio.fixture()
async def get_token() -> str:
    """Fixture to create an access token for testing authentication."""
    token = await auth_service.create_access_token(data={"sub": test_user["email"]})
    return token
