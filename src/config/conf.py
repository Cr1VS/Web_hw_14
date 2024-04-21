from typing import Any, Optional


from pydantic import ConfigDict, field_validator, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Class for secret data configurations.
    """

    DB_URL: str = "postgresql+asyncpg://postgres:1234509876@localhost:5432/web_hw_13"
    SECRET_KEY_JWT: str = "1234567890"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: EmailStr = "postgres@mail.com"
    MAIL_PASSWORD: str = "postgres"
    MAIL_FROM: str = "postgres"
    MAIL_PORT: int = 567234
    MAIL_SERVER: str = "postgres"
    REDIS_DOMAIN: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    CLD_NAME: str = "abc"
    CLD_API_KEY: int = 326488457974591
    CLD_API_SECRET: str = "secret"

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any) -> str:
        """
        Validates the JWT algorithm.

        Args:
            v (Any): The algorithm to validate.

        Returns:
            str: The validated algorithm.

        Raises:
            ValueError: If the algorithm is not HS256 or HS512.
        """
        if v not in ["HS256", "HS512"]:
            raise ValueError("Algorithm must be HS256 or HS512")
        return v

    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )  # noqa


config = Settings()
