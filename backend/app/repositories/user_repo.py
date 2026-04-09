from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import ShelterProfile, User, VolunteerProfile


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_volunteer(
    db: AsyncSession,
    email: str,
    password_hash: str,
    name: str,
    activity_regions: list[str],
) -> User:
    user = User(email=email, password_hash=password_hash, name=name, role="volunteer")
    db.add(user)
    await db.flush()

    profile = VolunteerProfile(
        user_id=user.id,
        vehicle_available=False,
        activity_regions=activity_regions,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user


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
    user = User(email=email, password_hash=password_hash, name=name, role="shelter")
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
    await db.refresh(user)
    return user
