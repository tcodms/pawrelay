import json
import logging
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


async def run_ai_decision_subscriber() -> None:
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("pawrelay:ai:decision")
    logger.info("AI decision subscriber started")
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload = json.loads(message["data"])
            await _handle_decision(payload)
        except Exception:
            logger.exception("Error handling AI decision: %s", message.get("data"))


async def _handle_decision(payload: dict) -> None:
    decision = payload.get("decision")
    segment_id = payload.get("segment_id")
    chain_id = payload.get("chain_id")
    volunteer_id = payload.get("volunteer_id")

    async with AsyncSessionLocal() as db:
        if decision == "no_show_candidate":
            await _handle_no_show(db, segment_id, volunteer_id)
        elif decision == "chain_break_candidate":
            await _handle_chain_break(db, chain_id)
        elif decision in ("shelter_recommend", "admin_alert", "rematch_candidate"):
            # 알림 모듈 연결 후 처리 (6주차 #133)
            logger.info("AI decision deferred: decision=%s segment_id=%s", decision, segment_id)
        else:
            logger.warning("Unknown AI decision: %s", decision)


async def _handle_no_show(db, segment_id: int, volunteer_id: int) -> None:
    from app.repositories import relay_repo, user_repo

    segment = await relay_repo.get_segment(db, segment_id)
    if not segment or segment.status in ("no_show", "completed"):
        return
    segment.status = "no_show"
    segment.declined_at = datetime.now(timezone.utc)

    user = await user_repo.get_user_by_id(db, volunteer_id)
    if user and user.account_status == "active":
        user.account_status = "suspended"

    await db.commit()


async def _handle_chain_break(db, chain_id: int) -> None:
    from sqlalchemy import select

    from app.models.relay import RelayChain
    from app.repositories import matching_repo

    result = await db.execute(select(RelayChain).where(RelayChain.id == chain_id))
    chain = result.scalars().first()
    if not chain or chain.status == "broken":
        return
    chain.status = "broken"
    await matching_repo.update_post_status(db, chain.transport_post_id, "recruiting")
    await db.commit()
