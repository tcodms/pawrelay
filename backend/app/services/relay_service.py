from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import relay_repo
from app.schemas.relay import CheckpointIn, CheckpointOut

_SEGMENT_STATUS_ON_DEPARTURE = "accepted"
_SEGMENT_STATUS_ACTIVE = "in_progress"
_SEGMENT_STATUS_DONE = "completed"


async def save_checkpoint(
    db: AsyncSession,
    user_id: int,
    body: CheckpointIn,
) -> CheckpointOut:
    segment = await relay_repo.get_segment(db, body.segment_id, lock=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})

    _validate_checkpoint_transition(segment.status, body.type)

    checkpoint = await relay_repo.create_checkpoint(
        db, body.segment_id, body.type, body.latitude, body.longitude
    )
    _apply_status_transition(segment, body.type)

    await db.commit()
    await db.refresh(checkpoint)
    return CheckpointOut(checkpoint_id=checkpoint.id, recorded_at=checkpoint.recorded_at)


def _validate_checkpoint_transition(segment_status: str, checkpoint_type: str) -> None:
    if checkpoint_type == "departure" and segment_status != _SEGMENT_STATUS_ON_DEPARTURE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})
    if checkpoint_type in ("waypoint", "arrival") and segment_status != _SEGMENT_STATUS_ACTIVE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})


def _apply_status_transition(segment, checkpoint_type: str) -> None:
    if checkpoint_type == "departure":
        segment.status = _SEGMENT_STATUS_ACTIVE
    elif checkpoint_type == "arrival":
        segment.status = _SEGMENT_STATUS_DONE
