from typing import AsyncGenerator

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_id(
    access_token: str | None = Cookie(default=None),
) -> int:
    if not access_token:
        raise HTTPException(status_code=401, detail={"error": "UNAUTHORIZED"})
    user_id = decode_access_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail={"error": "UNAUTHORIZED"})
    return user_id


async def get_optional_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not access_token:
        return None
    user_id = decode_access_token(access_token)
    if not user_id:
        return None
    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail={"error": "UNAUTHORIZED"})
    if user.account_status == "suspended":
        raise HTTPException(status_code=403, detail={"error": "ACCOUNT_SUSPENDED"})
    if user.account_status == "banned":
        raise HTTPException(status_code=403, detail={"error": "ACCOUNT_BANNED"})
    return user
