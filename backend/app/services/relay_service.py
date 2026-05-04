from datetime import datetime, timezone

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import relay_repo
from app.schemas.relay import CheckpointIn, CheckpointOut, HandoverVerifyIn, HandoverVerifyOut

_SEGMENT_STATUS_ON_DEPARTURE = "accepted"
_SEGMENT_STATUS_ACTIVE = "in_progress"
_SEGMENT_STATUS_DONE = "completed"

_RL_IP_LIMIT = 10
_RL_USER_LIMIT = 5
_RL_WINDOW = 60  # seconds


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


async def verify_handover(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    client_ip: str,
    body: HandoverVerifyIn,
) -> HandoverVerifyOut:
    await _check_handover_rate_limit(redis, user_id, client_ip)

    segment = await relay_repo.get_segment(db, body.segment_id, lock=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})

    next_segment = await relay_repo.get_next_segment(
        db, segment.chain_id, segment.segment_order, lock=True
    )

    is_giver = segment.volunteer_id == user_id
    is_receiver = next_segment and next_segment.volunteer_id == user_id
    if not is_giver and not is_receiver:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})

    if not segment.handover_code or segment.handover_code != body.code:
        raise HTTPException(status_code=400, detail={"error": "INVALID_CODE"})

    now = datetime.now(timezone.utc)
    if is_giver and not segment.handover_code_given_at:
        segment.handover_code_given_at = now
    elif is_receiver and not segment.handover_code_received_at:
        segment.handover_code_received_at = now

    both_confirmed = segment.handover_code_given_at and (
        segment.handover_code_received_at or next_segment is None
    )
    if both_confirmed:
        segment.status = _SEGMENT_STATUS_DONE
        segment.handover_method = "code"

    await db.commit()
    return HandoverVerifyOut(status="completed" if both_confirmed else "waiting_partner")


async def _check_handover_rate_limit(redis: Redis, user_id: int, client_ip: str) -> None:
    ip_key = f"rl:handover:ip:{client_ip}"
    user_key = f"rl:handover:user:{user_id}"

    ip_count = await redis.incr(ip_key)
    if ip_count == 1:
        await redis.expire(ip_key, _RL_WINDOW)

    user_count = await redis.incr(user_key)
    if user_count == 1:
        await redis.expire(user_key, _RL_WINDOW)

    if ip_count > _RL_IP_LIMIT or user_count > _RL_USER_LIMIT:
        raise HTTPException(status_code=429, detail={"error": "RATE_LIMIT_EXCEEDED"})


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
