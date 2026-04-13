from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
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

    result = await db.execute(
        select(TransportPost, func.coalesce(volunteer_count_subq.c.volunteer_count, 0))
        .outerjoin(volunteer_count_subq, TransportPost.id == volunteer_count_subq.c.post_id)
        .where(TransportPost.shelter_id == shelter_id)
        .order_by(TransportPost.scheduled_date.desc())
    )
    return result.all()
