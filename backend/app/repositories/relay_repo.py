from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relay import Checkpoint, RelaySegment


async def get_segment(db: AsyncSession, segment_id: int, lock: bool = False) -> RelaySegment | None:
    query = select(RelaySegment).where(RelaySegment.id == segment_id)
    if lock:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_next_segment(
    db: AsyncSession, chain_id: int, segment_order: int, lock: bool = False
) -> RelaySegment | None:
    query = select(RelaySegment).where(
        RelaySegment.chain_id == chain_id,
        RelaySegment.segment_order == segment_order + 1,
    )
    if lock:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def mark_stale_handovers_as_needs_verification(
    db: AsyncSession, cutoff: datetime
) -> int:
    """한쪽만 인계 코드 입력 후 cutoff 시간 이상 경과한 세그먼트를 needs_verification으로 전환."""
    stale_condition = or_(
        and_(
            RelaySegment.handover_code_given_at.isnot(None),
            RelaySegment.handover_code_received_at.is_(None),
            RelaySegment.handover_code_given_at <= cutoff,
        ),
        and_(
            RelaySegment.handover_code_received_at.isnot(None),
            RelaySegment.handover_code_given_at.is_(None),
            RelaySegment.handover_code_received_at <= cutoff,
        ),
    )
    result = await db.execute(
        update(RelaySegment)
        .where(RelaySegment.status == "in_progress", stale_condition)
        .values(status="needs_verification")
    )
    return result.rowcount


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
