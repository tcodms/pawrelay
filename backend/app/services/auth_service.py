from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import ShelterSignupRequest, VolunteerSignupRequest


def _set_auth_cookies(response: Response, user_id: int) -> None:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
    )


async def signup_volunteer(
    db: AsyncSession,
    body: VolunteerSignupRequest,
    response: Response,
) -> User:
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing:
        raise ValueError("EMAIL_ALREADY_EXISTS")

    user = await user_repo.create_volunteer(
        db=db,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        activity_regions=body.activity_regions,
    )
    _set_auth_cookies(response, user.id)
    return user


async def signup_shelter(
    db: AsyncSession,
    body: ShelterSignupRequest,
) -> User:
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing:
        raise ValueError("EMAIL_ALREADY_EXISTS")

    return await user_repo.create_shelter(
        db=db,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        phone=body.phone,
        contact_email=str(body.contact_email),
        address=body.address,
        shelter_registration_doc_url=body.shelter_registration_doc_url,
    )
