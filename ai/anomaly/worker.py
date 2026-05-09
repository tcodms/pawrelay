from ai.anomaly.publisher import publish_decision
from ai.anomaly.subscriber import create_pubsub
from ai.anomaly.subscriber import create_subscriber
from ai.anomaly.subscriber import decode_message
from ai.anomaly.subscriber import subscribe_inputs


async def route_event(channel, payload, handlers):
    handler = handlers[channel]
    return await handler(payload)


async def handle_message(message, handlers, publisher):
    decoded = decode_message(message)
    if decoded is None:
        return False
    channel, payload = decoded
    decision = await route_event(channel, payload, handlers)
    await publish_decision(publisher, decision)
    return True


async def run_worker(handlers, redis_url=None):
    subscriber = create_subscriber(redis_url)
    publisher = create_subscriber(redis_url)
    pubsub = create_pubsub(subscriber)
    await subscribe_inputs(pubsub)
    await _consume(pubsub, handlers, publisher)


async def _consume(pubsub, handlers, publisher):
    async for message in pubsub.listen():
        await handle_message(message, handlers, publisher)
