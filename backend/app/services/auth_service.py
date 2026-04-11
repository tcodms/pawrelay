from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.services.email_service import send_verification_email
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import LoginRequest, ShelterSignupRequest, VolunteerSignupRequest

_REFRESH_TOKEN_TTL = 60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS


async def _set_auth_cookies(response: Response, user_id: int) -> None:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    await redis_client.set(
        f"refresh_token:{user_id}",
        refresh_token,
        ex=_REFRESH_TOKEN_TTL,
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=_REFRESH_TOKEN_TTL,
    )


async def signup_volunteer(
    db: AsyncSession,
    body: VolunteerSignupRequest,
) -> User:
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing:
        raise ValueError("EMAIL_ALREADY_EXISTS")

    user = await user_repo.create_volunteer(
        db=db,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        vehicle_available=body.vehicle_available,
        max_animal_size=body.max_animal_size,
        activity_regions=body.activity_regions,
    )
    token = create_email_verification_token(user.id)
    await send_verification_email(body.email, token)
    return user


async def signup_shelter(
    db: AsyncSession,
    body: ShelterSignupRequest,
) -> User:
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing:
        raise ValueError("EMAIL_ALREADY_EXISTS")

    user = await user_repo.create_shelter(
        db=db,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        phone=body.phone,
        contact_email=str(body.contact_email),
        address=body.address,
        shelter_registration_doc_url=body.shelter_registration_doc_url,
    )
    token = create_email_verification_token(user.id)
    await send_verification_email(body.email, token)
    return user


async def verify_email(token: str, db: AsyncSession) -> None:
    user_id = decode_email_verification_token(token)
    if not user_id:
        raise ValueError("INVALID_VERIFICATION_TOKEN")
    await user_repo.verify_email(db, user_id)


async def login(
    db: AsyncSession,
    body: LoginRequest,
    response: Response,
) -> User:
    user = await user_repo.get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise ValueError("INVALID_CREDENTIALS")
    if user.account_status in ("suspended", "banned"):
        raise ValueError("ACCOUNT_SUSPENDED")
    if not user.email_verified_at:
        raise ValueError("EMAIL_NOT_VERIFIED")

    await _set_auth_cookies(response, user.id)
    return user


async def logout(response: Response, user_id: int) -> None:
    try:
        await redis_client.delete(f"refresh_token:{user_id}")
    except Exception:
        pass
    finally:
        response.delete_cookie("access_token", path="/", samesite="strict")
        response.delete_cookie("refresh_token", path="/", samesite="strict")


async def refresh(
    refresh_token: str | None,
    response: Response,
    db: AsyncSession,
) -> None:
    if not refresh_token:
        raise ValueError("REFRESH_TOKEN_EXPIRED")
    user_id = decode_refresh_token(refresh_token)
    if not user_id:
        raise ValueError("REFRESH_TOKEN_EXPIRED")

    stored_token = await redis_client.get(f"refresh_token:{user_id}")
    if not stored_token or stored_token != refresh_token:
        raise ValueError("REFRESH_TOKEN_EXPIRED")

    user = await user_repo.get_user_by_id(db, user_id)
    if not user or user.account_status in ("suspended", "banned"):
        raise ValueError("REFRESH_TOKEN_EXPIRED")

    await _set_auth_cookies(response, user_id)


async def revoke_refresh_token(user_id: int) -> None:
    await redis_client.delete(f"refresh_token:{user_id}")
