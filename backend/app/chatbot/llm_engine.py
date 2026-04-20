"""LLM 기반 챗봇 엔진 - ai.chatbot.engine.ChatbotEngine 래퍼.

MockChatbotEngine과 동일한 인터페이스를 제공하므로
chatbot_service.py는 엔진 교체를 인식할 필요가 없다.
"""
import json
from dataclasses import dataclass, field

from ai.chatbot.engine import ChatbotEngine


FIELD_STATE_MAP: dict[str, tuple[str, str | None, list[str] | None]] = {
    "origin": ("ASK_ORIGIN", "address_search", None),
    "destination": ("ASK_DESTINATION", "address_search", None),
    "available_date": ("ASK_DATE", "date_picker", None),
    "vehicle_available": ("ASK_VEHICLE", "buttons", ["있어요", "없어요"]),
    "max_animal_size": (
        "ASK_ANIMAL_SIZE",
        "buttons",
        ["소형 (5kg 이하)", "중형 (5~15kg)", "대형 (15kg 이상)"],
    ),
    "available_time": ("ASK_AVAILABLE_TIME", "text", None),
    "estimated_arrival_time": ("ASK_ESTIMATED_ARRIVAL_TIME", "text", None),
}

_CONFIRM_OPTIONS = ["등록하기", "처음부터 다시"]


@dataclass
class EngineResult:
    """LLM 엔진 처리 결과."""

    next_state: str
    message: str
    input_type: str | None
    options: list[str] | None
    collected_data: dict = field(default_factory=dict)
    completed: bool = False
    coordinates: dict = field(default_factory=dict)


def _extract_address_coords(message: str | None, state: str) -> tuple[str | None, dict]:
    """address_search 상태 메시지에서 주소 텍스트와 좌표를 분리한다.

    FE는 카카오 주소 검색 결과를 JSON으로 전송한다:
    '{"address": "광주광역시", "latitude": 35.15, "longitude": 126.85}'
    파싱 실패 시 원본 메시지를 그대로 사용한다.
    """
    if not message or state not in ("ASK_ORIGIN", "ASK_DESTINATION"):
        return message, {}
    try:
        data = json.loads(message)
        key = "origin" if state == "ASK_ORIGIN" else "destination"
        coords = {key: {"lat": data["latitude"], "lng": data["longitude"]}}
        return data["address"], coords
    except (json.JSONDecodeError, KeyError):
        return message, {}


def _restore_engine(
    state: str, collected_data: dict, post_id: int | None, auto_filled: dict
) -> ChatbotEngine:
    """세션 데이터로 ChatbotEngine 상태를 복원한다."""
    engine = ChatbotEngine(post_id=post_id, auto_filled=auto_filled)
    engine.collected_data = dict(collected_data)
    engine.state = "CONFIRMING" if state == "CONFIRM" else "COLLECTING"
    return engine


def _map_collecting(result: dict, coordinates: dict) -> EngineResult:
    """COLLECTING 결과를 API 스펙 state로 변환한다."""
    if result.get("error"):
        api_state = result.get("state", "COLLECTING")
        return EngineResult(api_state, result["message"], None, None, {}, False, coordinates)
    missing = result.get("missing_fields", [])
    if not missing:
        return EngineResult(
            "CONFIRM", result["message"], "buttons", _CONFIRM_OPTIONS,
            result.get("collected_data", {}), False, coordinates,
        )
    api_state, input_type, options = FIELD_STATE_MAP.get(
        missing[0], ("COLLECTING", None, None)
    )
    return EngineResult(
        api_state, result["message"], input_type, options,
        result.get("collected_data", {}), False, coordinates,
    )


def _map_result(result: dict, collected_data: dict, coordinates: dict) -> EngineResult:
    """ChatbotEngine 결과를 EngineResult로 변환한다."""
    state = result.get("state", "COLLECTING")
    if state == "COMPLETED":
        return EngineResult(
            "COMPLETED", result["message"], None, None, collected_data, True, coordinates
        )
    if state == "CONFIRMING":
        return EngineResult(
            "CONFIRM", result["message"], "buttons", _CONFIRM_OPTIONS,
            collected_data, False, coordinates,
        )
    return _map_collecting(result, coordinates)


class LLMChatbotEngine:
    """LLM 기반 챗봇 엔진. MockChatbotEngine과 동일한 인터페이스 제공."""

    async def process_input(
        self,
        message: str | None,
        state: str,
        collected_data: dict,
        post_id: int | None = None,
        auto_filled: dict | None = None,
    ) -> EngineResult:
        actual_message, coords = _extract_address_coords(message, state)
        engine = _restore_engine(state, collected_data, post_id, auto_filled or {})
        result = await engine.process_input(actual_message or "")
        return _map_result(result, engine.collected_data, coords)
