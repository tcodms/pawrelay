import logging
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo
from app.services import notification_service

logger = logging.getLogger(__name__)

_DEPARTURE_PING_WINDOW_HOURS = 2
_DEDUP_TTL_SECONDS = 3 * 3600  # 3시간 (중복 발송 방지)


async def send_departure_pings() -> None:
    """출발 2시간 이내인 accepted 세그먼트 봉사자에게 핑 발송"""
    cutoff = datetime.now(timezone.utc) + timedelta(hours=_DEPARTURE_PING_WINDOW_HOURS)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.get_accepted_segments_departing_soon(db, cutoff)
        count = 0
        for segment in segments:
            already_sent = not await redis_client.set(
                f"departure_ping_sent:{segment.id}", "1", nx=True, ex=_DEDUP_TTL_SECONDS
            )
            if already_sent:
                continue
            if not segment.volunteer:
                continue
            vol = segment.volunteer
            await notification_service.send_push_and_save(
                db, vol.id, vol.email, None,
                "ping_check", "출발 알림",
                f"출발 예정 시간이 2시간 이내입니다. 준비해 주세요.",
                {"segment_id": segment.id, "scheduled_time": segment.scheduled_time.isoformat()},
            )
            count += 1
        logger.info("[출발 핑] %d건 발송", count)
