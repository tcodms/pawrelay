import json

import pytest

from ai.anomaly.channels import BACKUP_EXHAUSTED_CHANNEL
from ai.anomaly.channels import CHECKPOINT_DELAY_CHANNEL
from ai.anomaly.channels import NEEDS_VERIFY_CHANNEL
from ai.anomaly.channels import PING_NO_RESPONSE_CHANNEL
from ai.anomaly.channels import PRE_DEPARTURE_NO_SHOW_CHANNEL
from ai.anomaly.channels import SOS_CHANNEL
from ai.anomaly.decision_engine import decide
from ai.anomaly.handlers import handle_backup_exhausted
from ai.anomaly.handlers import handle_checkpoint_delay
from ai.anomaly.handlers import handle_needs_verify
from ai.anomaly.handlers import handle_ping_no_response
from ai.anomaly.handlers import handle_pre_departure_no_show
from ai.anomaly.handlers import handle_sos


@pytest.mark.asyncio
async def test_handle_sos_returns_shelter_recommend(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    decision = await handle_sos(_sos_payload(), shelter_path=shelter_path)
    assert decision.decision == "shelter_recommend"
    assert decision.recommended_shelters[0].name == "\ucc9c\uc548\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c"


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
async def test_handle_backup_exhausted_returns_shelter_recommend(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    decision = await handle_backup_exhausted(_backup_payload(), shelter_path=shelter_path)
    assert decision.decision == "shelter_recommend"
    assert len(decision.recommended_shelters) == 1


@pytest.mark.asyncio
async def test_handle_ping_no_response_returns_admin_alert():
    decision = await handle_ping_no_response(_ping_payload())
    assert decision.decision == "admin_alert"
    assert "\ud551 \uc751\ub2f5" in decision.reason


@pytest.mark.asyncio
async def test_handle_pre_departure_no_show_returns_penalty_candidate():
    decision = await handle_pre_departure_no_show(_pre_departure_payload())
    assert decision.decision == "penalty_candidate"
    assert decision.requires_chain_break is True
    assert decision.penalty_days == 30
    assert "30\uc77c \uc815\uc9c0" in decision.reason


@pytest.mark.asyncio
async def test_decide_routes_backup_exhausted(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    decision = await decide(
        BACKUP_EXHAUSTED_CHANNEL,
        _backup_payload(),
        shelter_path=shelter_path,
    )
    assert decision.decision == "shelter_recommend"


@pytest.mark.asyncio
async def test_decide_routes_ping_no_response():
    decision = await decide(PING_NO_RESPONSE_CHANNEL, _ping_payload())
    assert decision.decision == "admin_alert"


@pytest.mark.asyncio
async def test_decide_routes_pre_departure_no_show():
    decision = await decide(PRE_DEPARTURE_NO_SHOW_CHANNEL, _pre_departure_payload())
    assert decision.decision == "penalty_candidate"


@pytest.mark.asyncio
async def test_decide_routes_by_original_channels(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    sos = await decide(SOS_CHANNEL, _sos_payload(), shelter_path=shelter_path)
    verify = await decide(NEEDS_VERIFY_CHANNEL, _needs_verify_payload())
    delay = await decide(CHECKPOINT_DELAY_CHANNEL, _checkpoint_payload(35))
    assert sos.decision == "shelter_recommend"
    assert verify.decision == "no_show_candidate"
    assert delay.decision == "reematch_candidate"


def _write_shelters(tmp_path):
    path = tmp_path / "shelter.json"
    payload = {
        "shelter": [
            _shelter(
                "\ucc9c\uc548\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c",
                "\ucda9\uccad\ub0a8\ub3c4 \ucc9c\uc548\uc2dc \ub3d9\ub0a8\uad6c",
            )
        ]
    }
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
        "activity_region": "\ucda9\ub0a8",
    }


def _needs_verify_payload():
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "Hong",
        "pickup_location": "Seoul",
        "dropoff_location": "Suwon Station",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "handover_code_given_at": "2026-05-07T15:05:00+09:00",
        "handover_code_received_at": None,
    }


def _checkpoint_payload(delay_minutes):
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "Hong",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "delay_minutes": delay_minutes,
        "last_checkpoint_type": None,
        "last_checkpoint_at": None,
        "latitude": None,
        "longitude": None,
    }


def _backup_payload():
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": None,
        "activity_regions": ["\ucda9\uccad\ub0a8\ub3c4"],
    }


def _ping_payload():
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "Hong",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "ping_sent_at": "2026-05-07T12:00:00+09:00",
        "ping_deadline_at": "2026-05-07T12:30:00+09:00",
        "activity_regions": ["\ucda9\ub0a8"],
    }


def _pre_departure_payload():
    return {
        "segment_id": 42,
        "chain_id": 7,
        "volunteer_id": 101,
        "volunteer_name": "Hong",
        "scheduled_time": "2026-05-07T14:00:00+09:00",
        "ping_sent_at": "2026-05-07T12:00:00+09:00",
        "ping_responded_at": None,
        "activity_regions": ["Chungcheongnam-do"],
    }
