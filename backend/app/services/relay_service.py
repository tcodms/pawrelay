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
    PingConfirmOut,
    SosIn, SosOut,
    WaypointInfo,
)
from app.services import notification_service, ws_service
from app.tasks.scheduler import scheduler
from app.tasks.sos_alert import send_delayed_sos_alert

_SEGMENT_STATUS_ON_DEPARTURE = "accepted"
_SEGMENT_STATUS_ACTIVE = "in_progress"
_SEGMENT_STATUS_DONE = "completed"

_RL_IP_LIMIT = 10
_RL_USER_LIMIT = 5
_RL_WINDOW = 60  # seconds

_SOS_ALERT_DELAY_MINUTES = 5


async def _get_authorized_segment_for_checkpoint(
    db: AsyncSession, segment_id: int, user_id: int, checkpoint_type: str
):
    segment = await relay_repo.get_segment(db, segment_id, lock=True, load_volunteer=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    _validate_checkpoint_transition(segment.status, checkpoint_type)
    return segment


async def save_checkpoint(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    body: CheckpointIn,
) -> CheckpointOut:
    segment = await _get_authorized_segment_for_checkpoint(db, body.segment_id, user_id, body.type)
    checkpoint = await relay_repo.create_checkpoint(
        db, body.segment_id, body.type, body.latitude, body.longitude
    )
    _apply_status_transition(segment, body.type)
    if body.type == "arrival":
        await _record_volunteer_history(db, segment)
    await db.commit()
    await db.refresh(checkpoint)
    await _publish_checkpoint_updated(db, redis, segment, checkpoint, body)
    if body.type == "arrival":
        await _notify_segment_completed(db, segment)
        await db.commit()
    return CheckpointOut(checkpoint_id=checkpoint.id, recorded_at=checkpoint.recorded_at)


async def verify_handover(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    client_ip: str,
    body: HandoverVerifyIn,
) -> HandoverVerifyOut:
    await _check_handover_rate_limit(redis, user_id, client_ip)

    segment = await relay_repo.get_segment(db, body.segment_id, lock=True, load_volunteer=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})

    next_segment = await relay_repo.get_next_segment(
        db, segment.chain_id, segment.segment_order, lock=True, load_volunteer=True
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

    # commit 전에 volunteer 정보 추출
    seg_id = segment.id
    giver_vol = (segment.volunteer.id, segment.volunteer.email) if segment.volunteer else None
    recv_vol = (next_segment.volunteer.id, next_segment.volunteer.email) if next_segment and next_segment.volunteer else None

    await db.commit()
    if not both_confirmed:
        await _notify_handover_waiting_confirm(db, seg_id, giver_vol, recv_vol, is_giver)
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

    chain_id, segment_order, segment_id = segment.chain_id, segment.segment_order, segment.id
    segment.ping_sent_at = datetime.now(timezone.utc)
    await db.commit()
    await _notify_ping_check(db, chain_id, segment_order, segment_id)
    return HandoverRequestOut(ok=True)


async def confirm_departure_ping(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    segment_id: int,
) -> PingConfirmOut:
    segment = await relay_repo.get_segment(db, segment_id, lock=True, load_volunteer=True)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    if segment.status != _SEGMENT_STATUS_ON_DEPARTURE:
        raise HTTPException(status_code=409, detail={"error": "INVALID_SEGMENT_STATUS"})
    if not segment.ping_sent_at:
        raise HTTPException(status_code=409, detail={"error": "PING_NOT_SENT"})
    if segment.ping_responded_at:
        await _publish_ping_confirmed(db, redis, segment)
        return PingConfirmOut(ok=True)
    segment.ping_responded_at = datetime.now(timezone.utc)
    await db.commit()
    await _publish_ping_confirmed(db, redis, segment)
    return PingConfirmOut(ok=True)


async def _validate_approve_handover(db: AsyncSession, segment_id: int, user_id: int):
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
    return segment


async def approve_handover(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    segment_id: int,
) -> HandoverApproveOut:
    segment = await _validate_approve_handover(db, segment_id, user_id)
    segment.ping_responded_at = datetime.now(timezone.utc)
    segment.status = _SEGMENT_STATUS_DONE
    segment.handover_method = "manual_approval"
    await db.commit()
    await _publish_ping_confirmed(db, redis, segment)
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

    chain_id, segment_order, segment_id = segment.chain_id, segment.segment_order, segment.id
    segment.dropoff_location = waypoint.name
    segment.waypoint_id = waypoint.id
    await db.commit()
    await _notify_handover_location_changed(db, chain_id, segment_order, segment_id, waypoint.name)
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
    await _publish_sos_ws_event(db, redis, segment, body)
    return SosOut(message="긴급 재매칭 요청이 접수되었습니다.")


async def _publish_checkpoint_updated(
    db: AsyncSession, redis: Redis, segment, checkpoint, body: CheckpointIn
) -> None:
    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return
    shelter_id, share_token = post_info
    await ws_service.publish_share_event(redis, str(share_token), "checkpoint.updated", {
        "segment_order": segment.segment_order,
        "latitude": body.latitude,
        "longitude": body.longitude,
        "recorded_at": checkpoint.recorded_at.isoformat(),
    })


async def _publish_ping_confirmed(db: AsyncSession, redis: Redis, segment) -> None:
    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return
    shelter_id, _ = post_info
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{segment.volunteer_id}"
    await ws_service.publish_user_event(redis, shelter_id, "ping.confirmed", {
        "segment_id": segment.id,
        "volunteer_name": volunteer_name,
    })


async def _publish_delay_reported(
    db: AsyncSession, redis: Redis, segment, message: str
) -> None:
    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return
    shelter_id, _ = post_info
    await ws_service.publish_user_event(redis, shelter_id, "delay.reported", {
        "segment_id": segment.id,
        "message": message,
    })


async def _publish_sos_ws_event(
    db: AsyncSession, redis: Redis, segment, body: SosIn
) -> None:
    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return
    shelter_id, _ = post_info
    await ws_service.publish_user_event(redis, shelter_id, "sos.triggered", {
        "segment_id": segment.id,
        "latitude": body.latitude,
        "longitude": body.longitude,
    })


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
    # SOS 잡은 단기 일회성이므로 memory jobstore 사용 (재시작 시 유실 허용)
    run_at = datetime.now(timezone.utc) + timedelta(minutes=_SOS_ALERT_DELAY_MINUTES)
    scheduler.add_job(
        send_delayed_sos_alert,
        trigger="date",
        run_date=run_at,
        jobstore="memory",
        kwargs={
            "segment_id": segment_id,
            "volunteer_name": volunteer_name,
            "latitude": latitude,
            "longitude": longitude,
        },
    )


async def report_delay(db: AsyncSession, redis: Redis, user_id: int, body: DelayIn) -> DelayOut:
    segment = await relay_repo.get_segment(db, body.segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})
    await _publish_delay_reported(db, redis, segment, body.message)
    await _notify_delay_reported_to_next_volunteer(db, segment, body.message)
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


async def _notify_delay_reported_to_next_volunteer(
    db: AsyncSession, segment, message: str
) -> None:
    next_seg = await relay_repo.get_next_segment(
        db, segment.chain_id, segment.segment_order, load_volunteer=True
    )
    if not next_seg or not next_seg.volunteer:
        return
    vol = next_seg.volunteer
    await notification_service.send_push_and_save(
        db, vol.id, vol.email, None,
        "delay_reported", "지연 신고",
        f"앞 구간 봉사자가 지연을 신고했습니다: {message}",
        {"segment_id": segment.id, "message": message},
    )


async def _notify_segment_completed(db: AsyncSession, segment) -> None:
    if not segment.volunteer:
        return
    vol = segment.volunteer
    await notification_service.save_in_app(
        db, vol.id, None,
        "segment_completed", "이동봉사 완료",
        "이동봉사 구간이 완료되었습니다. 수고하셨습니다!",
        {"segment_id": segment.id},
    )


async def _notify_ping_check(
    db: AsyncSession, chain_id: int, segment_order: int, segment_id: int
) -> None:
    next_seg = await relay_repo.get_next_segment(db, chain_id, segment_order, load_volunteer=True)
    if not next_seg or not next_seg.volunteer:
        return
    vol = next_seg.volunteer
    await notification_service.send_push_and_save(
        db, vol.id, vol.email, None,
        "ping_check", "인계 확인 요청", "앞 구간 봉사자가 인계를 요청했습니다.",
        {"segment_id": segment_id},
    )


async def _notify_handover_location_changed(
    db: AsyncSession, chain_id: int, segment_order: int, segment_id: int, new_location: str
) -> None:
    next_seg = await relay_repo.get_next_segment(db, chain_id, segment_order, load_volunteer=True)
    if not next_seg or not next_seg.volunteer:
        return
    vol = next_seg.volunteer
    await notification_service.send_push_and_save(
        db, vol.id, vol.email, None,
        "handover_location_changed", "인계 장소 변경",
        f"인계 장소가 '{new_location}'으로 변경되었습니다.",
        {"segment_id": segment_id, "new_location": new_location},
    )


async def _notify_handover_waiting_confirm(
    db: AsyncSession,
    segment_id: int,
    giver_vol: tuple[int, str] | None,
    recv_vol: tuple[int, str] | None,
    is_giver: bool,
) -> None:
    target = recv_vol if is_giver else giver_vol
    if not target:
        return
    vol_id, vol_email = target
    await notification_service.send_push_and_save(
        db, vol_id, vol_email, None,
        "handover_waiting_confirm", "인계 코드 입력 대기",
        "상대 봉사자가 인계 코드를 입력했습니다. 코드를 확인해주세요.",
        {"segment_id": segment_id},
    )
