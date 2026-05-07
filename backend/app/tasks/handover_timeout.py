import json
import os
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo

_HANDOVER_TIMEOUT_MINUTES = int(os.environ.get("NEEDS_VERIFY_GRACE_MINUTES", "30"))


async def mark_stale_handovers() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_HANDOVER_TIMEOUT_MINUTES)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.mark_stale_handovers_as_needs_verification(db, cutoff)
        if not segments:
            return
        payloads = [_build_needs_verify_payload(s) for s in segments]
        await db.commit()
    for payload in payloads:
        await redis_client.publish("pawrelay:needs_verify", json.dumps(payload))


def _build_needs_verify_payload(segment) -> dict:
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{segment.volunteer_id}"
    return {
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
