from datetime import datetime
from zoneinfo import ZoneInfo

from ai.anomaly.regions import normalize_region
from ai.anomaly.regions import normalize_regions
from ai.anomaly.schemas import AiDecisionEvent
from ai.anomaly.schemas import BackupExhaustedEvent
from ai.anomaly.schemas import CheckpointDelayEvent
from ai.anomaly.schemas import NeedsVerifyEvent
from ai.anomaly.schemas import PingNoResponseEvent
from ai.anomaly.schemas import PreDepartureNoShowEvent
from ai.anomaly.schemas import SosEvent
from ai.anomaly.settings import CHAIN_BREAK_DELAY_MINUTES
from ai.anomaly.settings import NO_SHOW_PENALTY_DAYS
from ai.anomaly.settings import RE_MATCH_DELAY_MINUTES
from ai.anomaly.shelter_recommender import recommend_shelters


def _detected_at():
    return datetime.now(ZoneInfo("Asia/Seoul"))


def _chain_id(event):
    return getattr(event, "chain_id", None)


def _regions(event):
    if hasattr(event, "activity_regions"):
        return normalize_regions(event.activity_regions)
    return [normalize_region(event.activity_region)]


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
        return "\uc778\uacc4 \ucf54\ub4dc\uac00 \ud55c\ucabd\uc5d0\uc11c\ub9cc \uc785\ub825\ub418\uc5b4 \ub178\uc1fc \ud6c4\ubcf4\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4."
    return "\uc778\uacc4 \ucf54\ub4dc \uc0c1\ud0dc\uac00 \ube44\uc815\uc0c1\uc774\ub77c \uad00\ub9ac\uc790 \ud655\uc778\uc774 \ud544\uc694\ud569\ub2c8\ub2e4."


def _delay_decision(delay_minutes):
    if delay_minutes >= CHAIN_BREAK_DELAY_MINUTES:
        return "chain_break_candidate"
    return "reematch_candidate"


def _delay_reason(event):
    if event.delay_minutes >= CHAIN_BREAK_DELAY_MINUTES:
        return f"\uc9c0\uc5f0 \uc2dc\uac04\uc774 {CHAIN_BREAK_DELAY_MINUTES}\ubd84 \uc774\uc0c1\uc774\ub77c \uccb4\uc778 \ud574\uc81c \ud6c4\ubcf4\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4."
    return f"\uc9c0\uc5f0 \uc2dc\uac04\uc774 {RE_MATCH_DELAY_MINUTES}\ubd84 \uc774\uc0c1\uc774\ub77c \uc7ac\ub9e4\uce6d \ud6c4\ubcf4\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4."


async def handle_sos(payload, shelter_path=None):
    event = SosEvent.model_validate(payload)
    shelters = _with_shelters(event, shelter_path)
    if shelters:
        return _decision("sos", event, "shelter_recommend", _sos_reason(True), shelters)
    return _decision("sos", event, "admin_alert", _sos_reason(False), [])


def _sos_reason(has_shelters):
    if has_shelters:
        return "SOS\uac00 \uc811\uc218\ub418\uc5b4 \uc784\uc2dc \ubcf4\ud638\uc18c \ud6c4\ubcf4\ub97c \ucd94\ucc9c\ud588\uc2b5\ub2c8\ub2e4."
    return "SOS\uac00 \uc811\uc218\ub418\uc5c8\uc9c0\ub9cc \ucd94\ucc9c \uac00\ub2a5\ud55c \uc784\uc2dc \ubcf4\ud638\uc18c\ub97c \ucc3e\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4."


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
        return "\ubc31\uc5c5 \ud6c4\ubcf4\uac00 \uc18c\uc9c4\ub418\uc5b4 \uc778\uadfc \ubcf4\ud638\uc18c \ud6c4\ubcf4\ub97c \ucd94\ucc9c\ud588\uc2b5\ub2c8\ub2e4."
    return "\ubc31\uc5c5 \ud6c4\ubcf4\uac00 \uc18c\uc9c4\ub418\uc5c8\uc9c0\ub9cc \ucd94\ucc9c \uac00\ub2a5\ud55c \ubcf4\ud638\uc18c\ub97c \ucc3e\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4."


async def handle_ping_no_response(payload, shelter_path=None):
    event = PingNoResponseEvent.model_validate(payload)
    return _decision(
        "ping_no_response",
        event,
        "admin_alert",
        "\ud551 \uc751\ub2f5\uc774 \uc5c6\uc5b4 \uad00\ub9ac\uc790 \ud655\uc778\uc774 \ud544\uc694\ud569\ub2c8\ub2e4.",
        [],
    )


async def handle_pre_departure_no_show(payload, shelter_path=None):
    event = PreDepartureNoShowEvent.model_validate(payload)
    return _decision(
        "pre_departure_no_show",
        event,
        "penalty_candidate",
        f"\ucd9c\ubc1c \uc804 \ub178\uc1fc\uac00 \uac10\uc9c0\ub418\uc5b4 \uccb4\uc778 \ud574\uc81c\uc640 {NO_SHOW_PENALTY_DAYS}\uc77c \uc815\uc9c0 \ud6c4\ubcf4\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4.",
        [],
        penalty_days=NO_SHOW_PENALTY_DAYS,
        requires_chain_break=True,
    )
