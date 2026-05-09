from datetime import datetime
from zoneinfo import ZoneInfo

from ai.anomaly.schemas import AiDecisionEvent
from ai.anomaly.schemas import BackupExhaustedEvent
from ai.anomaly.schemas import CheckpointDelayEvent
from ai.anomaly.schemas import NeedsVerifyEvent
from ai.anomaly.schemas import PingNoResponseEvent
from ai.anomaly.schemas import PreDepartureNoShowEvent
from ai.anomaly.schemas import SosEvent
from ai.anomaly.shelter_recommender import recommend_shelters


def _detected_at():
    return datetime.now(ZoneInfo("Asia/Seoul"))


def _chain_id(event):
    return getattr(event, "chain_id", None)


def _regions(event):
    if hasattr(event, "activity_regions"):
        return event.activity_regions
    return [event.activity_region]


def _decision(event_type, event, decision, reason, shelters, **extra):
    return AiDecisionEvent(
        event_type=event_type,
        segment_id=event.segment_id,
        chain_id=_chain_id(event),
        volunteer_id=getattr(event, "volunteer_id", None),
        decision=decision,
        reason=reason,
        recommended_shelters=shelters,
        detected_at=_detected_at(),
        **extra,
    )


def _with_shelters(event, shelter_path):
    return recommend_shelters(_regions(event), shelter_path)


def _is_one_sided(event):
    return bool(event.handover_code_given_at) != bool(event.handover_code_received_at)


def _needs_verify_decision(event):
    return "no_show_candidate" if _is_one_sided(event) else "admin_alert"


def _needs_verify_reason(event):
    if _is_one_sided(event):
        return "Only one side entered the handover code, so this is a no-show candidate."
    return "The handover code state is inconsistent and needs admin review."


def _delay_decision(delay_minutes):
    return "chain_break_candidate" if delay_minutes >= 60 else "reematch_candidate"


def _delay_reason(event):
    if event.delay_minutes >= 60:
        return "Delay is 60 minutes or more, so a chain break candidate is returned."
    return "Delay is 30 minutes or more, so a re-match candidate is returned."


async def handle_sos(payload, shelter_path=None):
    event = SosEvent.model_validate(payload)
    shelters = _with_shelters(event, shelter_path)
    if shelters:
        return _decision("sos", event, "shelter_recommend", _sos_reason(True), shelters)
    return _decision("sos", event, "admin_alert", _sos_reason(False), [])


def _sos_reason(has_shelters):
    if has_shelters:
        return "SOS was received and temporary shelter candidates were recommended."
    return "SOS was received but no temporary shelter candidate was found."


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


async def handle_backup_exhausted(payload, shelter_path=None):
    event = BackupExhaustedEvent.model_validate(payload)
    shelters = _with_shelters(event, shelter_path)
    reason = _backup_reason(bool(shelters))
    return _decision("backup_exhausted", event, _backup_decision(shelters), reason, shelters)


def _backup_decision(shelters):
    return "shelter_recommend" if shelters else "admin_alert"


def _backup_reason(has_shelters):
    if has_shelters:
        return "Backup candidates are exhausted, so nearby shelters are recommended."
    return "Backup candidates are exhausted and no nearby shelter candidate was found."


async def handle_ping_no_response(payload, shelter_path=None):
    event = PingNoResponseEvent.model_validate(payload)
    return _decision(
        "ping_no_response",
        event,
        "admin_alert",
        "A ping was not answered, so admin review is required.",
        [],
    )


async def handle_pre_departure_no_show(payload, shelter_path=None):
    event = PreDepartureNoShowEvent.model_validate(payload)
    return _decision(
        "pre_departure_no_show",
        event,
        "penalty_candidate",
        "A pre-departure no-show was detected, so chain break and 30-day penalty are requested.",
        [],
        penalty_days=30,
        requires_chain_break=True,
    )
