from datetime import datetime
from zoneinfo import ZoneInfo

from ai.anomaly.schemas import AiDecisionEvent
from ai.anomaly.schemas import CheckpointDelayEvent
from ai.anomaly.schemas import NeedsVerifyEvent
from ai.anomaly.schemas import SosEvent
from ai.anomaly.shelter_recommender import recommend_shelters


def _detected_at():
    return datetime.now(ZoneInfo("Asia/Seoul"))


def _chain_id(event):
    return getattr(event, "chain_id", None)


def _decision(event_type, event, decision, reason, shelters):
    return AiDecisionEvent(
        event_type=event_type,
        segment_id=event.segment_id,
        chain_id=_chain_id(event),
        volunteer_id=event.volunteer_id,
        decision=decision,
        reason=reason,
        recommended_shelters=shelters,
        detected_at=_detected_at(),
    )


def _needs_verify_decision(event):
    return "no_show_candidate" if _is_one_sided(event) else "admin_alert"


def _is_one_sided(event):
    return bool(event.handover_code_given_at) != bool(event.handover_code_received_at)


def _needs_verify_reason(event):
    if _is_one_sided(event):
        return "인계 코드 입력이 한쪽만 확인되어 노쇼 후보로 분류했습니다."
    return "인계 코드 상태가 비정상이라 관리자 확인이 필요합니다."


def _delay_decision(delay_minutes):
    return "chain_break_candidate" if delay_minutes >= 60 else "reematch_candidate"


def _delay_reason(event):
    if event.delay_minutes >= 60:
        return "지연 시간이 60분 이상이라 체인 해제 후보로 분류했습니다."
    return "지연 시간이 30분 이상이라 재매칭 후보로 분류했습니다."


async def handle_sos(payload, shelter_path=None):
    event = SosEvent.model_validate(payload)
    shelters = recommend_shelters([event.activity_region], shelter_path)
    if shelters:
        return _decision("sos", event, "shelter_recommend", "SOS 이벤트가 접수되어 임시 보호소 후보를 추천합니다.", shelters)
    return _decision("sos", event, "admin_alert", "SOS 이벤트가 접수되었지만 추천 가능한 보호소를 찾지 못했습니다.", [])


async def handle_needs_verify(payload, shelter_path=None):
    event = NeedsVerifyEvent.model_validate(payload)
    decision = _needs_verify_decision(event)
    reason = _needs_verify_reason(event)
    return _decision("needs_verify", event, decision, reason, [])


async def handle_checkpoint_delay(payload, shelter_path=None):
    event = CheckpointDelayEvent.model_validate(payload)
    decision = _delay_decision(event.delay_minutes)
    reason = _delay_reason(event)
    return _decision("checkpoint_delay", event, decision, reason, [])
