from dataclasses import dataclass, field
from datetime import date


STATE_SEQUENCE = [
    "ASK_ORIGIN",
    "ASK_DESTINATION",
    "ASK_DATE",
    "ASK_VEHICLE",
    "ASK_SIZE",
    "ASK_TIME",
    "COMPLETED",
]

STATE_PROMPTS: dict[str, tuple[str, str | None, list[str] | None]] = {
    "ASK_ORIGIN": ("어느 지역에서 출발하실 수 있나요?", "address_search", None),
    "ASK_DESTINATION": ("목적지는 어디인가요?", "address_search", None),
    "ASK_DATE": ("봉사 가능한 날짜를 선택해주세요.", "date_picker", None),
    "ASK_VEHICLE": ("차량이 있으신가요?", "buttons", ["있어요", "없어요"]),
    "ASK_SIZE": ("이동 가능한 동물 크기를 선택해주세요.", "buttons", ["소형", "중형", "대형"]),
    "ASK_TIME": ("출발 가능한 시간을 알려주세요. (예: 09:00, 건너뛰기)", None, None),
    "COMPLETED": ("일정 등록이 완료되었어요! 매칭 결과를 기다려주세요.", None, None),
}

SIZE_MAP = {"소형": "small", "중형": "medium", "대형": "large"}
VEHICLE_MAP = {"있어요": True, "없어요": False}


@dataclass
class EngineResult:
    next_state: str
    message: str
    input_type: str | None
    options: list[str] | None
    collected_data: dict = field(default_factory=dict)
    completed: bool = False


class MockChatbotEngine:
    def process_input(
        self,
        message: str | None,
        state: str,
        collected_data: dict,
    ) -> EngineResult:
        updated = dict(collected_data)

        if state == "ASK_ORIGIN" and message:
            updated["origin"] = message
            return self._build_result("ASK_DESTINATION", updated)

        if state == "ASK_DESTINATION" and message:
            updated["destination"] = message
            return self._build_result("ASK_DATE", updated)

        if state == "ASK_DATE" and message:
            updated["available_date"] = message
            return self._build_result("ASK_VEHICLE", updated)

        if state == "ASK_VEHICLE" and message:
            updated["vehicle_available"] = VEHICLE_MAP.get(message, False)
            return self._build_result("ASK_SIZE", updated)

        if state == "ASK_SIZE" and message:
            updated["max_animal_size"] = SIZE_MAP.get(message, "small")
            return self._build_result("ASK_TIME", updated)

        if state == "ASK_TIME":
            if message and message != "건너뛰기":
                updated["available_time"] = message
            return self._build_completed_result(updated)

        # 현재 state 질문 반환 (메시지 없거나 첫 진입)
        return self._build_result(state, updated)

    def _build_result(self, state: str, collected_data: dict) -> EngineResult:
        msg, input_type, options = STATE_PROMPTS[state]
        return EngineResult(
            next_state=state,
            message=msg,
            input_type=input_type,
            options=options,
            collected_data=collected_data,
            completed=False,
        )

    def _build_completed_result(self, collected_data: dict) -> EngineResult:
        msg, _, _ = STATE_PROMPTS["COMPLETED"]
        return EngineResult(
            next_state="COMPLETED",
            message=msg,
            input_type=None,
            options=None,
            collected_data=collected_data,
            completed=True,
        )
