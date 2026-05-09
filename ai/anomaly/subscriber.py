import json
import os

from ai.anomaly.channels import INPUT_CHANNELS


def _redis_url(redis_url=None):
    return redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")


def create_subscriber(redis_url=None):
    import redis.asyncio as aioredis

    return aioredis.from_url(_redis_url(redis_url), decode_responses=True)


def create_pubsub(client):
    return client.pubsub()


async def subscribe_inputs(pubsub):
    await pubsub.subscribe(*INPUT_CHANNELS)


def decode_message(message):
    if message.get("type") != "message":
        return None
    channel = message["channel"]
    payload = json.loads(message["data"])
    return channel, payload
