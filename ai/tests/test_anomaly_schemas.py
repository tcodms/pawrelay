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
        activity_region="Chungcheongnam-do",
    )
    assert event.segment_id == 1
    assert event.activity_region == "Chungcheongnam-do"


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
        activity_regions=["Chungcheongnam-do", "Daejeon"],
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
        activity_regions=["Chungcheongnam-do"],
    )
    assert event.volunteer_id == 101
    assert event.activity_regions == ["Chungcheongnam-do"]


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
        reason="Delay exceeded threshold.",
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
        name="Cheonan Shelter",
        address="Chungcheongnam-do Cheonan",
        phone="041-000-0000",
    )
