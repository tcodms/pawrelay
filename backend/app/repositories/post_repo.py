from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.relay import Checkpoint, RelayChain, RelaySegment
from app.models.user import User
from app.models.volunteer import VolunteerSchedule


async def get_dashboard_posts(db: AsyncSession, shelter_id: int) -> list[tuple]:
    volunteer_count_subq = (
        select(
            VolunteerSchedule.post_id,
            func.count(VolunteerSchedule.id).label("volunteer_count"),
        )
        .where(VolunteerSchedule.status == "available")
        .group_by(VolunteerSchedule.post_id)
        .subquery()
    )

    chain_subq = (
        select(
            RelayChain.transport_post_id,
            func.max(RelayChain.id).label("chain_id"),
        )
        .where(RelayChain.status.in_(["proposed", "active"]))
        .group_by(RelayChain.transport_post_id)
        .subquery()
    )

    result = await db.execute(
        select(
            TransportPost,
            func.coalesce(volunteer_count_subq.c.volunteer_count, 0),
            chain_subq.c.chain_id,
            RelayChain.matching_reason,
            RelayChain.chain_expires_at,
        )
        .outerjoin(volunteer_count_subq, TransportPost.id == volunteer_count_subq.c.post_id)
        .outerjoin(chain_subq, TransportPost.id == chain_subq.c.transport_post_id)
        .outerjoin(RelayChain, RelayChain.id == chain_subq.c.chain_id)
        .where(TransportPost.shelter_id == shelter_id)
        .order_by(TransportPost.scheduled_date.desc())
    )
    return result.all()


async def get_segments_for_chains(db: AsyncSession, chain_ids: list[int]) -> dict[int, list]:
    if not chain_ids:
        return {}
    result = await db.execute(
        select(RelaySegment, User.name)
        .join(User, RelaySegment.volunteer_id == User.id)
        .where(RelaySegment.chain_id.in_(chain_ids))
        .order_by(RelaySegment.chain_id, RelaySegment.segment_order)
    )
    segments_by_chain: dict[int, list] = {}
    for segment, volunteer_name in result.all():
        segments_by_chain.setdefault(segment.chain_id, []).append({
            "volunteer_name": volunteer_name,
            "from_area": segment.pickup_location,
            "to_area": segment.dropoff_location,
            "depart_time": segment.scheduled_time.strftime("%H:%M") if segment.scheduled_time else None,
        })
    return segments_by_chain


async def create_post(
    db: AsyncSession,
    shelter_id: int,
    origin: str,
    destination: str,
    scheduled_date,
    animal_name: str,
    animal_size: str,
    animal_photo_url: str | None,
    animal_notes: str | None,
) -> TransportPost:
    post = TransportPost(
        shelter_id=shelter_id,
        origin=origin,
        destination=destination,
        scheduled_date=scheduled_date,
        animal_name=animal_name,
        animal_size=animal_size,
        animal_photo_url=animal_photo_url,
        animal_notes=animal_notes,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def get_posts(
    db: AsyncSession,
    region: str | None,
    date,
    animal_size: str | None,
    page: int,
    limit: int,
) -> tuple[list[TransportPost], int]:
    query = select(TransportPost).where(TransportPost.status == "recruiting")

    if region:
        query = query.where(
            TransportPost.origin.ilike(f"%{region}%")
            | TransportPost.destination.ilike(f"%{region}%")
        )
    if date:
        query = query.where(TransportPost.scheduled_date == date)
    if animal_size:
        query = query.where(TransportPost.animal_size == animal_size)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(TransportPost.scheduled_date.asc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_post_by_id(db: AsyncSession, post_id: int) -> TransportPost | None:
    result = await db.execute(select(TransportPost).where(TransportPost.id == post_id))
    return result.scalar_one_or_none()


async def get_volunteers_for_post(db: AsyncSession, post_id: int) -> list[tuple[int, str, str, str]]:
    result = await db.execute(
        select(User.id, User.name, VolunteerSchedule.origin_area, VolunteerSchedule.destination_area)
        .join(VolunteerSchedule, User.id == VolunteerSchedule.volunteer_id)
        .where(VolunteerSchedule.post_id == post_id)
        .where(VolunteerSchedule.status == "available")
    )
    return result.all()


async def count_volunteers_for_post(db: AsyncSession, post_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(VolunteerSchedule)
        .where(VolunteerSchedule.post_id == post_id)
        .where(VolunteerSchedule.status == "available")
    )
    return result.scalar_one()


async def get_post_by_share_token(db: AsyncSession, share_token: UUID) -> TransportPost | None:
    result = await db.execute(
        select(TransportPost).where(TransportPost.share_token == share_token)
    )
    return result.scalar_one_or_none()


async def update_post(
    db: AsyncSession,
    post_id: int,
    scheduled_date=None,
    animal_notes=None,
    animal_notes_provided: bool = False,
) -> bool:
    values = {}
    if scheduled_date is not None:
        values["scheduled_date"] = scheduled_date
    if animal_notes_provided:
        values["animal_notes"] = animal_notes

    if not values:
        return True

    result = await db.execute(
        update(TransportPost)
        .where(TransportPost.id == post_id, TransportPost.status == "recruiting")
        .values(**values)
    )
    await db.commit()
    return result.rowcount > 0


async def cancel_post(db: AsyncSession, post_id: int) -> bool:
    result = await db.execute(
        update(TransportPost)
        .where(TransportPost.id == post_id, TransportPost.status == "recruiting")
        .values(status="cancelled")
    )
    await db.commit()
    return result.rowcount > 0


async def get_public_post_data(
    db: AsyncSession, post: TransportPost
) -> tuple[RelaySegment | None, list[Checkpoint], list[RelaySegment]]:
    chain_result = await db.execute(
        select(RelayChain)
        .where(RelayChain.transport_post_id == post.id)
        .where(RelayChain.status == "active")
    )
    chain = chain_result.scalar_one_or_none()

    if not chain:
        return None, [], []

    segments_result = await db.execute(
        select(RelaySegment)
        .where(RelaySegment.chain_id == chain.id)
        .order_by(RelaySegment.segment_order.asc())
    )
    segments = segments_result.scalars().all()

    current_segment = next(
        (s for s in segments if s.status == "in_progress"), None
    )

    segment_ids = [s.id for s in segments]
    checkpoints_result = await db.execute(
        select(Checkpoint)
        .where(Checkpoint.segment_id.in_(segment_ids))
        .order_by(Checkpoint.recorded_at.asc())
    )
    checkpoints = checkpoints_result.scalars().all()

    completed_segments = [s for s in segments if s.status == "completed"]

    return current_segment, checkpoints, completed_segments
