import pytest

from pydantic import ValidationError

from ai.anomaly.schemas import (
    AiDecisionEvent,
    CheckpointDelayEvent,
    NeedsVerifyEvent,
    RecommendedShelter,
    SosEvent,
)


def test_parse_sos_event():
    event = SosEvent(
        segment_id=1,
        volunteer_id=42,
        latitude=36.35,
        longitude=127.38,
        activity_region="충청남도",
    )
    assert event.segment_id == 1
    assert event.activity_region == "충청남도"


def test_parse_needs_verify_event():
    event = NeedsVerifyEvent(
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        volunteer_name="홍길동",
        pickup_location="서울 강남구 역삼동",
        dropoff_location="수원역 1번 출구",
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
        volunteer_name="홍길동",
        scheduled_time="2026-05-07T14:00:00+09:00",
        delay_minutes=35,
    )
    assert event.delay_minutes == 35
    assert event.last_checkpoint_type is None


def test_parse_ai_decision_event():
    event = AiDecisionEvent(
        event_type="checkpoint_delay",
        segment_id=42,
        chain_id=7,
        volunteer_id=101,
        decision="chain_break_candidate",
        reason="scheduled_time 기준 35분 경과했고 checkpoint 기록이 없습니다.",
        recommended_shelters=[_sample_shelter()],
        detected_at="2026-05-07T14:35:00+09:00",
    )
    assert event.decision == "chain_break_candidate"
    assert len(event.recommended_shelters) == 1


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
        name="천안시 유기동물보호소",
        address="충청남도 천안시 ...",
        phone="041-000-0000",
    )
