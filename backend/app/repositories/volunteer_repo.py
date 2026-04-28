from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.volunteer import VolunteerSchedule


async def create_schedule(
    db: AsyncSession,
    volunteer_id: int,
    post_id: int | None,
    route_description: str,
    origin_area: str,
    destination_area: str,
    available_date: date,
    available_time: str | None,
    estimated_arrival_time: str | None,
    vehicle_available: bool,
    max_animal_size: str,
    route_wkt: str | None,
) -> VolunteerSchedule:
    schedule = VolunteerSchedule(
        volunteer_id=volunteer_id,
        post_id=post_id,
        route_description=route_description,
        origin_area=origin_area,
        destination_area=destination_area,
        available_date=available_date,
        available_time=available_time,
        estimated_arrival_time=estimated_arrival_time,
        vehicle_available=vehicle_available,
        max_animal_size=max_animal_size,
        route=route_wkt,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def get_schedules_by_volunteer(db: AsyncSession, volunteer_id: int) -> list[VolunteerSchedule]:
    result = await db.execute(
        select(VolunteerSchedule)
        .where(VolunteerSchedule.volunteer_id == volunteer_id)
        .options(selectinload(VolunteerSchedule.post))
        .order_by(VolunteerSchedule.available_date.desc())
    )
    return list(result.scalars().all())
