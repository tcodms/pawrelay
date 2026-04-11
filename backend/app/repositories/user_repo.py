from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import ShelterProfile, User, VolunteerProfile


def _is_email_unique_violation(e: IntegrityError) -> bool:
    return "users_email_key" in str(e.orig) or "ix_users_email" in str(e.orig)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    normalized = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_volunteer(
    db: AsyncSession,
    email: str,
    password_hash: str,
    name: str,
    vehicle_available: bool,
    max_animal_size: str,
    activity_regions: list[str],
) -> User:
    try:
        user = User(email=email.strip().lower(), password_hash=password_hash, name=name, role="volunteer")
        db.add(user)
        await db.flush()

        profile = VolunteerProfile(
            user_id=user.id,
            vehicle_available=vehicle_available,
            max_animal_size=max_animal_size,
            activity_regions=activity_regions,
        )
        db.add(profile)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if _is_email_unique_violation(e):
            raise ValueError("EMAIL_ALREADY_EXISTS") from e
        raise
    await db.refresh(user)
    return user


async def verify_email(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    if not user.email_verified_at:
        user.email_verified_at = datetime.now(timezone.utc)
        await db.commit()
    return True


async def create_shelter(
    db: AsyncSession,
    email: str,
    password_hash: str,
    name: str,
    phone: str,
    contact_email: str,
    address: str,
    shelter_registration_doc_url: str | None,
) -> User:
    try:
        user = User(email=email.strip().lower(), password_hash=password_hash, name=name, role="shelter")
        db.add(user)
        await db.flush()

        profile = ShelterProfile(
            user_id=user.id,
            name=name,
            phone=phone,
            email=contact_email,
            address=address,
            shelter_registration_doc_url=shelter_registration_doc_url,
        )
        db.add(profile)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if _is_email_unique_violation(e):
            raise ValueError("EMAIL_ALREADY_EXISTS") from e
        raise
    await db.refresh(user)
    return user
