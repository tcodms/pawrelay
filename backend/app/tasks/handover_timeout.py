import json
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo

_HANDOVER_TIMEOUT_MINUTES = 30


async def mark_stale_handovers() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_HANDOVER_TIMEOUT_MINUTES)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.mark_stale_handovers_as_needs_verification(db, cutoff)
        if segments:
            await db.commit()
            for segment in segments:
                await _publish_needs_verify(segment)


async def _publish_needs_verify(segment) -> None:
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{segment.volunteer_id}"
    payload = {
        "segment_id": segment.id,
        "chain_id": segment.chain_id,
        "volunteer_id": segment.volunteer_id,
        "volunteer_name": volunteer_name,
        "pickup_location": segment.pickup_location,
        "dropoff_location": segment.dropoff_location,
        "scheduled_time": segment.scheduled_time.isoformat() if segment.scheduled_time else None,
        "handover_code_given_at": segment.handover_code_given_at.isoformat() if segment.handover_code_given_at else None,
        "handover_code_received_at": segment.handover_code_received_at.isoformat() if segment.handover_code_received_at else None,
    }
    await redis_client.publish("pawrelay:needs_verify", json.dumps(payload))
