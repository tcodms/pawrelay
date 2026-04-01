from .states import (
    ChatState,
    STATE_CONFIG,
    STATE_ORDER,
    SKIP_STATES_WITH_POST,
)


# 입력값 → DB 저장용 변환 매핑
VEHICLE_MAP = {"있어요": True, "없어요": False}
ANIMAL_SIZE_MAP = {
    "소형 (5kg 이하)": "small",
    "중형 (5~15kg)": "medium",
    "대형 (15kg 이상)": "large",
}


class ChatbotEngine:
    """챗봇 상태 머신 엔진.

    LLM 없이 사전 정의된 상태 순서대로 질문하고,
    봉사자의 동선 정보를 수집한다.
    """

    def __init__(self, post_id=None, auto_filled=None):
        self.post_id = post_id
        self.auto_filled = auto_filled or {}
        self.collected_data = {}
        self.current_state = self._find_first_state()

    def _should_skip(self, state):
        """post_id가 있을 때 해당 상태를 건너뛸지 판단."""
        if self.post_id and state in SKIP_STATES_WITH_POST:
            return True
        return False

    def _find_first_state(self):
        """첫 번째로 질문할 상태를 찾는다."""
        for state in STATE_ORDER:
            if not self._should_skip(state):
                return state
        return ChatState.COMPLETED

    def _find_next_state(self):
        """현재 상태 다음으로 질문할 상태를 찾는다."""
        current_index = STATE_ORDER.index(self.current_state)

        for state in STATE_ORDER[current_index + 1:]:
            if not self._should_skip(state):
                return state
        return ChatState.COMPLETED

    def get_current_response(self):
        """현재 상태에 맞는 응답을 반환한다."""
        config = STATE_CONFIG[self.current_state]

        return {
            "state": self.current_state.value,
            "message": config["message"],
            "input_type": config["input_type"],
            "options": config["options"],
            "auto_filled": self.auto_filled if self.post_id else None,
            "completed": self.current_state == ChatState.COMPLETED,
        }

    def process_input(self, user_input):
        """사용자 입력을 처리하고 다음 상태로 전이한다."""
        validation_error = self._validate_input(user_input)
        if validation_error:
            return {
                "state": self.current_state.value,
                "message": validation_error,
                "input_type": STATE_CONFIG[self.current_state]["input_type"],
                "options": STATE_CONFIG[self.current_state]["options"],
                "auto_filled": self.auto_filled if self.post_id else None,
                "completed": False,
                "error": "INVALID_INPUT",
            }

        self._save_input(user_input)

        if self.current_state == ChatState.CONFIRM:
            return self._handle_confirm(user_input)

        self.current_state = self._find_next_state()
        return self.get_current_response()

    def _validate_input(self, user_input):
        """입력값 검증. 문제 있으면 에러 메시지 반환."""
        if not user_input or not user_input.strip():
            return "입력값이 비어있습니다. 다시 입력해주세요."

        state = self.current_state
        config = STATE_CONFIG[state]

        if config["options"] and user_input not in config["options"]:
            return "보기 중에서 선택해주세요."

        return None

    def _save_input(self, user_input):
        """현재 상태에 맞는 키로 입력값을 저장한다."""
        save_map = {
            ChatState.ASK_ORIGIN: "origin",
            ChatState.ASK_DESTINATION: "destination",
            ChatState.ASK_DATE: "available_date",
            ChatState.ASK_VEHICLE: "vehicle_available",
            ChatState.ASK_ANIMAL_SIZE: "max_animal_size",
        }

        key = save_map.get(self.current_state)
        if not key:
            return

        if self.current_state == ChatState.ASK_VEHICLE:
            self.collected_data[key] = VEHICLE_MAP[user_input]
        elif self.current_state == ChatState.ASK_ANIMAL_SIZE:
            self.collected_data[key] = ANIMAL_SIZE_MAP[user_input]
        else:
            self.collected_data[key] = user_input

    def _handle_confirm(self, user_input):
        """확인 단계 처리."""
        if user_input == "처음부터 다시":
            self.collected_data = {}
            self.current_state = self._find_first_state()
            return self.get_current_response()

        self.current_state = ChatState.COMPLETED
        return {
            **self.get_current_response(),
            "schedule_data": self.get_schedule_data(),
        }

    def get_schedule_data(self):
        """DB 저장용 데이터를 반환한다."""
        data = {**self.collected_data}

        if self.post_id:
            data["post_id"] = self.post_id

        if self.auto_filled:
            if "available_date" not in data:
                data["available_date"] = self.auto_filled.get("available_date")
            if "max_animal_size" not in data:
                data["max_animal_size"] = self.auto_filled.get("max_animal_size")

        return data