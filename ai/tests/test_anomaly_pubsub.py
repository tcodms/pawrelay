import json

import pytest

from ai.anomaly.channels import CHECKPOINT_DELAY_CHANNEL
from ai.anomaly.channels import DECISION_CHANNEL
from ai.anomaly.channels import INPUT_CHANNELS
from ai.anomaly.publisher import serialize_decision
from ai.anomaly.schemas import AiDecisionEvent
from ai.anomaly.subscriber import decode_message
from ai.anomaly.worker import handle_message


def test_input_channels_count():
    assert len(INPUT_CHANNELS) == 6


def test_decode_message_ignores_subscribe_event():
    message = {"type": "subscribe", "channel": "x", "data": "1"}
    assert decode_message(message) is None


def test_decode_message_parses_payload():
    payload = {"segment_id": 42, "delay_minutes": 35}
    message = _message(payload)
    decoded = decode_message(message)
    assert decoded[0] == CHECKPOINT_DELAY_CHANNEL
    assert decoded[1]["segment_id"] == 42


def test_serialize_decision_contains_decision():
    decision = _decision()
    payload = serialize_decision(decision)
    assert "chain_break_candidate" in payload


@pytest.mark.asyncio
async def test_handle_message_publishes_decision():
    publisher = FakePublisher()
    handlers = {CHECKPOINT_DELAY_CHANNEL: _fake_handler}
    handled = await handle_message(_message({"segment_id": 42}), handlers, publisher)
    assert handled is True
    assert publisher.channel == DECISION_CHANNEL
    assert "chain_break_candidate" in publisher.payload


def _message(payload):
    return {
        "type": "message",
        "channel": CHECKPOINT_DELAY_CHANNEL,
        "data": json.dumps(payload, ensure_ascii=False),
    }


def _decision():
    return AiDecisionEvent(
        event_type="checkpoint_delay",
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        decision="chain_break_candidate",
        reason="Delay exceeded threshold.",
        detected_at="2026-05-07T14:35:00+09:00",
    )


async def _fake_handler(payload):
    assert payload["segment_id"] == 42
    return _decision()


class FakePublisher:
    channel = None
    payload = None

    async def publish(self, channel, payload):
        self.channel = channel
        self.payload = payload
