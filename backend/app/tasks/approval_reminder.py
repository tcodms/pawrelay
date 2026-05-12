import logging
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import matching_repo
from app.services import ws_service

logger = logging.getLogger(__name__)

_REMINDER_THRESHOLD_HOURS = 12
_DEDUP_TTL_SECONDS = 2 * 3600  # 2시간 (중복 발송 방지)


async def send_approval_reminders() -> None:
    """chain_expires_at까지 12시간 이하 남은 proposed 체인 보호소에 재알림"""
    cutoff = datetime.now(timezone.utc) + timedelta(hours=_REMINDER_THRESHOLD_HOURS)
    async with AsyncSessionLocal() as db:
        chains = await matching_repo.get_expiring_chains(db, cutoff)
        count = 0
        for chain in chains:
            already_sent = not await redis_client.set(
                f"approval_reminder_sent:{chain.id}", "1", nx=True, ex=_DEDUP_TTL_SECONDS
            )
            if already_sent:
                continue
            shelter_id = chain.transport_post.shelter_id
            await ws_service.publish_user_event(
                redis_client, shelter_id, "matching.approval_reminder",
                {
                    "chain_id": chain.id,
                    "expires_at": chain.chain_expires_at.isoformat() if chain.chain_expires_at else None,
                },
            )
            count += 1
        logger.info("[승인 리마인더] %d건 발송", count)
