import pytest

from pydantic import ValidationError

from ai.anomaly.schemas import AiDecisionEvent
from ai.anomaly.schemas import BackupExhaustedEvent
from ai.anomaly.schemas import CheckpointDelayEvent
from ai.anomaly.schemas import NeedsVerifyEvent
from ai.anomaly.schemas import PingNoResponseEvent
from ai.anomaly.schemas import PreDepartureNoShowEvent
from ai.anomaly.schemas import RecommendedShelter
from ai.anomaly.schemas import SosEvent


def test_parse_sos_event():
    event = SosEvent(
        segment_id=1,
        volunteer_id=42,
        latitude=36.35,
        longitude=127.38,
        activity_region="\ucda9\ub0a8",
    )
    assert event.segment_id == 1
    assert event.activity_region == "\ucda9\ub0a8"


def test_parse_needs_verify_event():
    event = NeedsVerifyEvent(
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        volunteer_name="Hong",
        pickup_location="Seoul",
        dropoff_location="Suwon Station",
        scheduled_time="2026-05-07T14:00:00+09:00",
        handover_code_given_at="2026-05-07T15:05:00+09:00",
    )
    assert event.chain_id == 7
    assert event.handover_code_received_at is None


def test_parse_checkpoint_delay_event():
    event = CheckpointDelayEvent(
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        volunteer_name="Hong",
        scheduled_time="2026-05-07T14:00:00+09:00",
        delay_minutes=35,
    )
    assert event.delay_minutes == 35
    assert event.last_checkpoint_type is None


def test_parse_backup_exhausted_event():
    event = BackupExhaustedEvent(
        segment_id=42,
        chain_id=7,
        activity_regions=["\ucda9\ub0a8", "\ub300\uc804"],
    )
    assert event.volunteer_id is None
    assert len(event.activity_regions) == 2


def test_parse_ping_no_response_event():
    event = PingNoResponseEvent(
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        volunteer_name="Hong",
        scheduled_time="2026-05-07T14:00:00+09:00",
        ping_sent_at="2026-05-07T12:00:00+09:00",
        ping_deadline_at="2026-05-07T12:30:00+09:00",
        activity_regions=["\ucda9\uccad\ub0a8\ub3c4"],
    )
    assert event.volunteer_id == 101
    assert event.activity_regions == ["\ucda9\uccad\ub0a8\ub3c4"]


def test_parse_pre_departure_no_show_event():
    event = PreDepartureNoShowEvent(
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        volunteer_name="Hong",
        scheduled_time="2026-05-07T14:00:00+09:00",
        ping_sent_at="2026-05-07T12:00:00+09:00",
        ping_responded_at=None,
        activity_regions=["Chungcheongnam-do"],
    )
    assert event.chain_id == 7
    assert event.ping_responded_at is None


def test_parse_ai_decision_event():
    event = AiDecisionEvent(
        event_type="checkpoint_delay",
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        decision="chain_break_candidate",
        reason="\uc9c0\uc5f0 \uc2dc\uac04\uc774 \uae30\uc900\uce58\ub97c \ub118\uc5b4 \uccb4\uc778 \ud574\uc81c \ud6c4\ubcf4\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4.",
        recommended_shelters=[_sample_shelter()],
        requires_chain_break=True,
        penalty_days=None,
        detected_at="2026-05-07T14:35:00+09:00",
    )
    assert event.decision == "chain_break_candidate"
    assert len(event.recommended_shelters) == 1
    assert event.requires_chain_break is True


def test_reject_invalid_decision():
    with pytest.raises(ValidationError):
        AiDecisionEvent(
            event_type="sos",
            segment_id=1,
            volunteer_id=42,
            decision="wrong",
            reason="invalid",
            detected_at="2026-05-07T14:35:00+09:00",
        )


def _sample_shelter():
    return RecommendedShelter(
        name="\ucc9c\uc548\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c",
        address="\ucda9\uccad\ub0a8\ub3c4 \ucc9c\uc548\uc2dc",
        phone="041-000-0000",
    )
