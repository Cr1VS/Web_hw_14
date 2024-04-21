import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter


from schemas.consumer import (
    UserSchema,
    TokenSchema,
    UserResponse,
    RequestEmail,
    PasswordForm,
)
from services.email import send_email, send_password_email
from repository import consumers as repository_consumer
from services.auth import auth_service
from database.db import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Parameters:
    - `body`: Data of the new user.
    - `bt`: Background tasks to be executed.
    - `request`: The request object.
    - `db`: The database session.

    Returns the created user.
    """
    exist_user = await repository_consumer.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_consumer.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    User login.

    Parameters:
    - `body`: Data for user authentication.
    - `db`: The database session.

    Returns access tokens.
    """
    user = await repository_consumer.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(
        data={"sub": user.email, "test": "Tester Testorovich"}
    )
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_consumer.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get(
    "/refresh_token",
    response_model=TokenSchema,
    dependencies=[Depends(RateLimiter(times=2, seconds=10))],
)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh the access token.

    Parameters:
    - `credentials`: Authentication data.
    - `db`: The database session.

    Returns the updated access tokens.
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_consumer.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_consumer.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_consumer.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm the user's email.

    Parameters:
    - `token`: The confirmation token.
    - `db`: The database session.

    Returns a message indicating the confirmation status.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_consumer.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_consumer.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email", dependencies=[Depends(RateLimiter(times=2, seconds=10))])
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request email confirmation.

    Parameters:
    - `body`: Request email data.
    - `background_tasks`: Background tasks to be executed.
    - `request`: The request object.
    - `db`: The database session.

    Returns a message indicating the email confirmation status.
    """
    user = await repository_consumer.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.get("/new-password/{token}")
async def new_password(token: str, db: AsyncSession = Depends(get_db)):
    """
    Reset the user's password.

    Parameters:
    - `token`: The reset password token.
    - `db`: The database session.

    Returns a message indicating the status of the password reset.
    """
    email = await auth_service.get_email_from_token(token)
    password = await auth_service.get_password_from_token(token)
    user = await repository_consumer.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if password:
        password = auth_service.get_password_hash(password)
        await repository_consumer.update_password(email, password, db)
    return {"message": "New password successfully updated!"}


@router.post(
    "/reset-password", dependencies=[Depends(RateLimiter(times=2, seconds=10))]
)
async def reset_password(
    body: PasswordForm,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset the user's password.

    Parameters:
    - `body`: Password reset data.
    - `background_tasks`: Background tasks to be executed.
    - `request`: The request object.
    - `db`: The database session.

    Returns a message indicating the status of the password reset request.
    """
    user = await repository_consumer.get_user_by_email(body.email, db)
    if user:
        if body.password == body.password_confirm:
            background_tasks.add_task(
                send_password_email,
                user.email,
                user.username,
                body.password,
                str(request.base_url),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Passwords do not match!",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Such email does not exist!",
        )

    return {"message": "Check your email, link for password reset was sent."}
