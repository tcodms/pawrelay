import json
import logging

from app.core.redis import redis_client
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def run_ws_subscriber() -> None:
    pubsub = redis_client.pubsub()
    try:
        await pubsub.psubscribe("pawrelay:ws:*")
        logger.info("WebSocket Redis subscriber started")
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            try:
                channel: str = message["channel"]
                data = json.loads(message["data"])
                if ":user:" in channel:
                    user_id = int(channel.rsplit(":", 1)[-1])
                    await manager.send_to_user(user_id, data)
                elif ":share:" in channel:
                    share_token = channel.split("pawrelay:ws:share:")[-1]
                    await manager.send_to_share(share_token, data)
            except Exception:
                logger.exception("WebSocket subscriber 처리 오류")
    finally:
        await pubsub.punsubscribe("pawrelay:ws:*")
        await pubsub.close()
