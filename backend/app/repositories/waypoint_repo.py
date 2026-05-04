from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.waypoint import Waypoint


async def get_waypoint(db: AsyncSession, waypoint_id: int) -> Waypoint | None:
    result = await db.execute(select(Waypoint).where(Waypoint.id == waypoint_id))
    return result.scalar_one_or_none()
