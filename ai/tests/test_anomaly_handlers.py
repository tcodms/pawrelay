import json

import pytest

from ai.anomaly.channels import CHECKPOINT_DELAY_CHANNEL
from ai.anomaly.channels import NEEDS_VERIFY_CHANNEL
from ai.anomaly.channels import SOS_CHANNEL
from ai.anomaly.decision_engine import decide
from ai.anomaly.handlers import handle_checkpoint_delay
from ai.anomaly.handlers import handle_needs_verify
from ai.anomaly.handlers import handle_sos


@pytest.mark.asyncio
async def test_handle_sos_returns_shelter_recommend(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    decision = await handle_sos(_sos_payload(), shelter_path=shelter_path)
    assert decision.decision == "shelter_recommend"
    assert decision.recommended_shelters[0].name == "천안시 유기동물보호소"


@pytest.mark.asyncio
async def test_handle_needs_verify_returns_no_show_candidate():
    decision = await handle_needs_verify(_needs_verify_payload())
    assert decision.decision == "no_show_candidate"


@pytest.mark.asyncio
async def test_handle_checkpoint_delay_returns_reematch_candidate():
    decision = await handle_checkpoint_delay(_checkpoint_payload(35))
    assert decision.decision == "reematch_candidate"


@pytest.mark.asyncio
async def test_handle_checkpoint_delay_returns_chain_break_candidate():
    decision = await handle_checkpoint_delay(_checkpoint_payload(65))
    assert decision.decision == "chain_break_candidate"


@pytest.mark.asyncio
async def test_decide_routes_by_channel(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    decision = await decide(SOS_CHANNEL, _sos_payload(), shelter_path=shelter_path)
    assert decision.decision == "shelter_recommend"


def _write_shelters(tmp_path):
    path = tmp_path / "shelter.json"
    payload = {"shelter": [_shelter("천안시 유기동물보호소", "충청남도 천안시 동남구")]}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _shelter(name, address):
    return {"name": name, "address": address, "phone": "041-000-0000"}


def _sos_payload():
    return {
        "segment_id": 1,
        "volunteer_id": 42,
        "latitude": 36.35,
        "longitude": 127.38,
        "activity_region": "충청남도",
    }


def _needs_verify_payload():
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "홍길동",
        "pickup_location": "서울 강남구 역삼동",
        "dropoff_location": "수원역 1번 출구",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "handover_code_given_at": "2026-05-07T15:05:00+09:00",
        "handover_code_received_at": None,
    }


def _checkpoint_payload(delay_minutes):
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "홍길동",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "delay_minutes": delay_minutes,
        "last_checkpoint_type": None,
        "last_checkpoint_at": None,
        "latitude": None,
        "longitude": None,
    }
