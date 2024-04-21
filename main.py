from ipaddress import ip_address
from typing import Callable
import re


from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from sqlalchemy import text


from src.customs.custom_logger import logger
from src.routes import user_profile
from src.database.db import get_db
from src.config.conf import config
from src.routes import users
from src.routes import auth


app = FastAPI()


banned_ips = [
    ip_address("192.168.1.1"),
]


origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


user_agent_ban_list = [r"Python-urllib"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response


app.include_router(auth.router, prefix="/api")
app.include_router(user_profile.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.on_event("startup")
async def startup():
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)


@app.get("/")
def index() -> dict:
    """
    Main endpoint returning a message indicating the Todo Application.
    """
    return {"message": "Todo Application"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Endpoint for checking the health of the application and database connection.

    Args:
        db (AsyncSession): An asynchronous database session.

    Returns:
        dict: A message indicating the status of the application and database connection.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        logger.log(e, level=40)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
