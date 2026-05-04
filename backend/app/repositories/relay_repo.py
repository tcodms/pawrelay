from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relay import Checkpoint, RelaySegment


async def get_segment(db: AsyncSession, segment_id: int, lock: bool = False) -> RelaySegment | None:
    query = select(RelaySegment).where(RelaySegment.id == segment_id)
    if lock:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_checkpoint(
    db: AsyncSession,
    segment_id: int,
    checkpoint_type: str,
    latitude: float | None,
    longitude: float | None,
) -> Checkpoint:
    checkpoint = Checkpoint(
        segment_id=segment_id,
        type=checkpoint_type,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(checkpoint)
    await db.flush()
    return checkpoint
