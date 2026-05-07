import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from redis.asyncio import Redis

logger = logging.getLogger(__name__)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.volunteer import VolunteerHistory
from app.repositories import relay_repo, waypoint_repo
from app.schemas.relay import (
    CheckpointIn, CheckpointOut,
    DelayIn, DelayOut,
    HandoverApproveOut, HandoverLocationIn, HandoverLocationOut,
    HandoverRequestOut, HandoverVerifyIn, HandoverVerifyOut,
    SosIn, SosOut,
    WaypointInfo,
)
from app.tasks.scheduler import scheduler
from app.tasks.sos_alert import send_delayed_sos_alert

_SEGMENT_STATUS_ON_DEPARTURE = "accepted"
_SEGMENT_STATUS_ACTIVE = "in_progress"
_SEGMENT_STATUS_DONE = "completed"

_RL_IP_LIMIT = 10
_RL_USER_LIMIT = 5
_RL_WINDOW = 60  # seconds

_SOS_ALERT_DELAY_MINUTES = 5


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
    if body.type == "arrival":
        await _record_volunteer_history(db, segment)

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


async def request_handover(
    db: AsyncSession,
    user_id: int,
    segment_id: int,
) -> HandoverRequestOut:
    segment = await relay_repo.get_segment(db, segment_id, lock=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    if segment.status != _SEGMENT_STATUS_ACTIVE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})

    segment.ping_sent_at = datetime.now(timezone.utc)
    await db.commit()
    # 알림 전송은 6주차 알림 모듈 완성 후 연결
    return HandoverRequestOut(ok=True)


async def approve_handover(
    db: AsyncSession,
    user_id: int,
    segment_id: int,
) -> HandoverApproveOut:
    segment = await relay_repo.get_segment(db, segment_id, lock=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})

    next_segment = await relay_repo.get_next_segment(
        db, segment.chain_id, segment.segment_order, lock=True
    )
    if not next_segment or next_segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    if segment.status != _SEGMENT_STATUS_ACTIVE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})
    if not segment.ping_sent_at:
        raise HTTPException(status_code=409, detail={"error": "HANDOVER_NOT_REQUESTED"})

    segment.ping_responded_at = datetime.now(timezone.utc)
    segment.status = _SEGMENT_STATUS_DONE
    segment.handover_method = "manual_approval"
    await db.commit()
    return HandoverApproveOut(status=_SEGMENT_STATUS_DONE)


async def update_handover_location(
    db: AsyncSession,
    user_id: int,
    segment_id: int,
    body: HandoverLocationIn,
) -> HandoverLocationOut:
    segment = await relay_repo.get_segment(db, segment_id, lock=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED_SEGMENT"})

    if segment.status == _SEGMENT_STATUS_DONE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})

    waypoint = await waypoint_repo.get_waypoint(db, body.waypoint_id)
    if not waypoint:
        raise HTTPException(status_code=404, detail={"error": "WAYPOINT_NOT_FOUND"})

    segment.dropoff_location = waypoint.name
    segment.waypoint_id = waypoint.id
    await db.commit()
    # 뒷구간 봉사자 Web Push는 6주차 알림 모듈 완성 후 연결
    return HandoverLocationOut(dropoff_location=WaypointInfo(name=waypoint.name, address=waypoint.address))


async def report_sos(db: AsyncSession, redis: Redis, user_id: int, body: SosIn) -> SosOut:
    segment = await relay_repo.get_segment(db, body.segment_id, load_volunteer=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})

    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{user_id}"
    _schedule_sos_alert(body.segment_id, volunteer_name, body.latitude, body.longitude)
    await _publish_sos_event(redis, segment, volunteer_name, body)
    return SosOut(message="긴급 재매칭 요청이 접수되었습니다.")


async def _record_volunteer_history(db: AsyncSession, segment) -> None:
    stmt = pg_insert(VolunteerHistory).values(
        volunteer_id=segment.volunteer_id,
        segment_id=segment.id,
        distance_km=0,
        completed_at=datetime.now(timezone.utc),
    ).on_conflict_do_nothing(index_elements=["segment_id"])
    await db.execute(stmt)


async def _publish_sos_event(redis: Redis, segment, volunteer_name: str, body: SosIn) -> None:
    payload = {
        "segment_id": segment.id,
        "chain_id": segment.chain_id,
        "volunteer_id": segment.volunteer_id,
        "volunteer_name": volunteer_name,
        "latitude": body.latitude,
        "longitude": body.longitude,
    }
    try:
        await redis.publish("pawrelay:sos", json.dumps(payload, ensure_ascii=False))
    except Exception:
        logger.exception("SOS Redis publish 실패: segment_id=%s", segment.id)


def _schedule_sos_alert(
    segment_id: int,
    volunteer_name: str,
    latitude: float | None,
    longitude: float | None,
) -> None:
    # TODO: 영속 jobstore(RedisJobStore/SQLAlchemyJobStore) 적용 필요 — 현재 메모리 기반으로 재시작 시 잡 유실 가능
    run_at = datetime.now(timezone.utc) + timedelta(minutes=_SOS_ALERT_DELAY_MINUTES)
    scheduler.add_job(
        send_delayed_sos_alert,
        trigger="date",
        run_date=run_at,
        kwargs={
            "segment_id": segment_id,
            "volunteer_name": volunteer_name,
            "latitude": latitude,
            "longitude": longitude,
        },
    )


async def report_delay(db: AsyncSession, user_id: int, body: DelayIn) -> DelayOut:
    segment = await relay_repo.get_segment(db, body.segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    # 다음 구간 봉사자 + 보호소 알림은 6주차 알림 모듈 완성 후 연결
    return DelayOut(ok=True)


async def _check_handover_rate_limit(redis: Redis, user_id: int, client_ip: str) -> None:
    ip_key = f"rl:handover:ip:{client_ip}"
    user_key = f"rl:handover:user:{user_id}"

    async with redis.pipeline(transaction=False) as pipe:
        pipe.incr(ip_key)
        pipe.expire(ip_key, _RL_WINDOW, nx=True)  # TTL 없을 때만 세팅 (고정 윈도우)
        pipe.incr(user_key)
        pipe.expire(user_key, _RL_WINDOW, nx=True)
        ip_count, _, user_count, _ = await pipe.execute()

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
