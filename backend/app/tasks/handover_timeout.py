import json
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import relay_repo
from app.services import notification_service, ws_service

_HANDOVER_TIMEOUT_MINUTES = int(os.environ.get("NEEDS_VERIFY_GRACE_MINUTES", "30"))


async def mark_stale_handovers() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_HANDOVER_TIMEOUT_MINUTES)
    async with AsyncSessionLocal() as db:
        segments = await relay_repo.mark_stale_handovers_as_needs_verification(db, cutoff)
        if not segments:
            return
        payloads = [_build_needs_verify_payload(s) for s in segments]
        post_infos = {
            s.id: await relay_repo.get_post_info_by_chain(db, s.chain_id)
            for s in segments
        }
        await db.commit()
        await _publish_needs_verify_events(db, segments, payloads, post_infos)


async def _publish_needs_verify_events(db, segments, payloads, post_infos) -> None:
    for segment, payload in zip(segments, payloads, strict=True):
        try:
            await redis_client.publish("pawrelay:needs_verify", json.dumps(payload))
            info = post_infos.get(segment.id)
            if not info:
                continue
            shelter_id, _ = info
            ws_payload = {
                "segment_id": segment.id,
                "volunteer_name": payload["volunteer_name"],
                "scheduled_time": payload["scheduled_time"],
            }
            await ws_service.publish_user_event(redis_client, shelter_id, "handover.no_response", ws_payload)
            await notification_service.save_in_app(
                db, shelter_id, None,
                "handover_no_response", "인계 코드 미응답",
                f"{payload['volunteer_name']} 봉사자가 인계 코드를 입력하지 않았습니다.",
                ws_payload,
            )
        except Exception:
            logger.exception("segment_id=%s 알림 발행 실패", segment.id)
    await db.commit()


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
