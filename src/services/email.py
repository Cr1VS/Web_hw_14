from typing import Awaitable
from pathlib import Path
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr


from customs.custom_logger import logger
from services.auth import auth_service
from config.conf import config


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_USERNAME,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="TODO Systems",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str) -> Awaitable[None]:
    """
    Sends an email for email address confirmation.

    :param email: Recipient's email address.
    :type email: EmailStr
    :param username: The username to be used in the email template.
    :type username: str
    :param host: The host to be used in the email template.
    :type host: str
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as e:
        logger.log(e, level=40)


async def send_password_email(
    email: EmailStr, username: str, password: str, host: str
) -> Awaitable[None]:
    """
    Sends an email for password reset.

    :param email: Recipient's email address.
    :type email: EmailStr
    :param username: The username to be used in the email template.
    :type username: str
    :param password: The password to be used in the email template.
    :type password: str
    :param host: The host to be used in the email template.
    :type host: str
    """
    try:
        token_verification = auth_service.create_email_token(
            {"sub": email, "password": password}
        )
        message = MessageSchema(
            subject="Password reset form",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_form.html")
    except ConnectionErrors as e:
        logger.log(e, level=40)
