import json
import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_USER_CHANNEL = "pawrelay:ws:user:{user_id}"
_SHARE_CHANNEL = "pawrelay:ws:share:{share_token}"


async def publish_user_event(redis: Redis, user_id: int, event: str, payload: dict) -> None:
    data = json.dumps({"event": event, "payload": payload}, ensure_ascii=False)
    try:
        await redis.publish(_USER_CHANNEL.format(user_id=user_id), data)
    except Exception:
        logger.exception("WS user event publish 실패: user_id=%s event=%s", user_id, event)


async def publish_share_event(redis: Redis, share_token: str, event: str, payload: dict) -> None:
    data = json.dumps({"event": event, "payload": payload}, ensure_ascii=False)
    try:
        await redis.publish(_SHARE_CHANNEL.format(share_token=share_token), data)
    except Exception:
        logger.exception("WS share event publish 실패: share_token=%s event=%s", share_token, event)
