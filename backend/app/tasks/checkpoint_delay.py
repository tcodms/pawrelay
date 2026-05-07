import json
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo

_CHECKPOINT_DELAY_MINUTES = 30


async def detect_checkpoint_delays() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_CHECKPOINT_DELAY_MINUTES)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.get_delayed_segments(db, cutoff)
        for segment in segments:
            already_notified = not await redis_client.set(
                f"checkpoint_delay_notified:{segment.id}",
                "1",
                nx=True,
                ex=3600,
            )
            if not already_notified:
                await _publish_checkpoint_delay(segment)


async def _publish_checkpoint_delay(segment) -> None:
    now = datetime.now(timezone.utc)
    scheduled = segment.scheduled_time
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    delay_minutes = int((now - scheduled).total_seconds() / 60)
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{segment.volunteer_id}"
    payload = {
        "segment_id": segment.id,
        "chain_id": segment.chain_id,
        "volunteer_id": segment.volunteer_id,
        "volunteer_name": volunteer_name,
        "scheduled_time": segment.scheduled_time.isoformat(),
        "delay_minutes": delay_minutes,
        "last_checkpoint_type": None,
        "last_checkpoint_at": None,
        "latitude": None,
        "longitude": None,
    }
    await redis_client.publish("pawrelay:checkpoint_delay", json.dumps(payload))
