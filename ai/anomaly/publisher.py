import os

from ai.anomaly.channels import DECISION_CHANNEL
from ai.anomaly.schemas import AiDecisionEvent


def _redis_url(redis_url=None):
    return redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")


def create_publisher(redis_url=None):
    import redis.asyncio as aioredis

    return aioredis.from_url(_redis_url(redis_url), decode_responses=True)


def serialize_decision(decision):
    return decision.model_dump_json()


async def publish_decision(client, decision):
    payload = serialize_decision(decision)
    await client.publish(DECISION_CHANNEL, payload)
