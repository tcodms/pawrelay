import json
import logging
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo
from app.services import notification_service, ws_service

logger = logging.getLogger(__name__)

_DEPARTURE_NO_RESPONSE_WINDOW_HOURS = 1
_DEDUP_TTL_SECONDS = 3 * 3600


async def send_departure_no_response_alerts() -> None:
    cutoff = datetime.now(timezone.utc) + timedelta(hours=_DEPARTURE_NO_RESPONSE_WINDOW_HOURS)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.get_accepted_segments_ping_no_response(db, cutoff)
        count = 0
        for segment in segments:
            try:
                if await _alert_for_segment(db, segment):
                    count += 1
            except Exception:
                logger.exception("segment_id=%s 출발 핑 미응답 알림 발행 실패", segment.id)
        logger.info("[출발 핑 미응답] %d건 경고 발행", count)


async def _alert_for_segment(db, segment) -> bool:
    if await _already_alerted(segment.id):
        return False
    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return False
    shelter_id, _ = post_info
    volunteer_name = _volunteer_name(segment)
    ws_payload, ai_payload = _build_payloads(segment, volunteer_name)
    await _publish_alerts(db, shelter_id, volunteer_name, ws_payload, ai_payload)
    await db.commit()
    return True


async def _already_alerted(segment_id: int) -> bool:
    return not await redis_client.set(
        f"departure_no_response_sent:{segment_id}", "1", nx=True, ex=_DEDUP_TTL_SECONDS
    )


def _volunteer_name(segment) -> str:
    if segment.volunteer:
        return segment.volunteer.name
    return f"봉사자#{segment.volunteer_id}"


def _build_payloads(segment, volunteer_name: str) -> tuple[dict, dict]:
    scheduled_time = segment.scheduled_time.isoformat() if segment.scheduled_time else None
    ws_payload = {
        "segment_id": segment.id,
        "volunteer_name": volunteer_name,
        "scheduled_time": scheduled_time,
    }
    ai_payload = {
        "segment_id": segment.id,
        "chain_id": segment.chain_id,
        "volunteer_id": segment.volunteer_id,
        "volunteer_name": volunteer_name,
        "scheduled_time": scheduled_time,
    }
    return ws_payload, ai_payload


async def _publish_alerts(
    db,
    shelter_id: int,
    volunteer_name: str,
    ws_payload: dict,
    ai_payload: dict,
) -> None:
    await redis_client.publish("pawrelay:ping_no_response", json.dumps(ai_payload))
    await ws_service.publish_user_event(redis_client, shelter_id, "departure.no_response", ws_payload)
    await notification_service.save_in_app(
        db,
        shelter_id,
        None,
        "departure_no_response",
        "출발 전 핑 미응답",
        f"{volunteer_name} 봉사자가 출발 알림에 응답하지 않았습니다.",
        ws_payload,
    )
