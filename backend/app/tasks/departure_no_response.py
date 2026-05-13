import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo
from app.services import notification_service, ws_service

_DEPARTURE_NO_RESPONSE_WINDOW_HOURS = 1
_DEDUP_TTL_SECONDS = 3 * 3600  # 3시간 (중복 발송 방지)


async def send_departure_no_response_alerts() -> None:
    """출발 1시간 전까지 핑 미응답인 봉사자 → 보호소 주황 경고"""
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
    already_sent = not await redis_client.set(
        f"departure_no_response_sent:{segment.id}", "1", nx=True, ex=_DEDUP_TTL_SECONDS
    )
    if already_sent:
        return False

    post_info = await relay_repo.get_post_info_by_chain(db, segment.chain_id)
    if not post_info:
        return False

    shelter_id, _ = post_info
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{segment.volunteer_id}"
    ws_payload = {
        "segment_id": segment.id,
        "volunteer_name": volunteer_name,
        "scheduled_time": segment.scheduled_time.isoformat() if segment.scheduled_time else None,
    }
    await redis_client.publish("pawrelay:ping_no_response", json.dumps({
        "segment_id": segment.id,
        "volunteer_id": segment.volunteer_id,
        "volunteer_name": volunteer_name,
        "scheduled_time": segment.scheduled_time.isoformat() if segment.scheduled_time else None,
    }))
    await ws_service.publish_user_event(redis_client, shelter_id, "departure.no_response", ws_payload)
    await notification_service.save_in_app(
        db, shelter_id, None,
        "departure_no_response", "출발 전 핑 미응답",
        f"{volunteer_name} 봉사자가 출발 알림에 응답하지 않았습니다.",
        ws_payload,
    )
    await db.commit()
    return True
