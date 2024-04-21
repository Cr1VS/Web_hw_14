import pickle


from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    UploadFile,
    File,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary.uploader
import cloudinary


from src.repository import consumers as repository_consumer
from schemas.consumer import UserResponse
from services.auth import auth_service
from entity.models import Consumer
from database.db import get_db
from config.conf import config


router = APIRouter(prefix="/users-profile", tags=["users-profile"])


cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=2, seconds=10))],
)
async def get_current_user(user: Consumer = Depends(auth_service.get_current_user)):
    return user


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=2, seconds=10))],
)
async def update_avatar(
    file: UploadFile = File(),
    user: Consumer = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        public_id = f"Web16/{user.email}"
        res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        res_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=res.get("version")
        )
        user = await repository_consumer.update_avatar_url(user.email, res_url, db)
        auth_service.cache.set(user.email, pickle.dumps(user))
        auth_service.cache.expire(user.email, 300)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar. Please try again later.",
        ) from e
