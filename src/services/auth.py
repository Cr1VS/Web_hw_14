from datetime import datetime, timedelta, timezone
from typing import Optional
import pickle
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import JWTError, jwt
import redis


from repository.consumers import get_user_by_email
from customs.custom_logger import logger
from database.db import get_db
from config.conf import config


class Auth:
    """
    Class for user authentication and authorization.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies if a password matches its hashed version.

        Args:
            plain_password (str): The password in plain text.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Generates a password hash.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ) -> str:
        """
        Creates an access token.

        Args:
            data (dict): Data to include in the token.
            expires_delta (Optional[float]): Optional expiration time in seconds.

        Returns:
            str: The encoded access token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.now(timezone.utc), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ) -> str:
        """
        Creates a refresh token.

        Args:
            data (dict): Data to include in the token.
            expires_delta (Optional[float]): Optional expiration time in seconds.

        Returns:
            str: The encoded refresh token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.now(timezone.utc), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str) -> str:
        """
        Decodes a refresh token.

        Args:
            refresh_token (str): The refresh token to decode.

        Returns:
            str: The email associated with the refresh token.

        Raises:
            HTTPException: If the token scope is invalid.
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ) -> dict:
        """
        Gets the current authenticated user.

        Args:
            token (str, optional): The authentication token.
            db (AsyncSession, optional): The database session.

        Returns:
            User: The current authenticated user.

        Raises:
            HTTPException: If the credentials are invalid or the user is not found.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    def create_email_token(self, data: dict) -> str:
        """
        Creates a JWT token for email verification.

        Args:
            data (dict): Data to be encoded into the token.

        Returns:
            str: The encoded JWT token.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=1)
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str) -> str:
        """
        Extracts email from a JWT token.

        Args:
            token (str): The JWT token containing email information.

        Returns:
            str: The email extracted from the token.

        Raises:
            HTTPException: If the token is invalid for email verification.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            logger.log(e, level=40)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

    async def get_password_from_token(self, token: str) -> str:
        """
        Extracts password from a JWT token.

        Args:
            token (str): The JWT token containing password information.

        Returns:
            str: The password extracted from the token.

        Raises:
            HTTPException: If the token is invalid for password verification.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            password = payload["password"]
            return password
        except JWTError as e:
            logger.log(e, level=40)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for password verification",
            )


auth_service = Auth()
