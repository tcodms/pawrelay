import json
import zoneinfo
from datetime import datetime

from ai.providers import get_llm_provider
from .parser import (
    parse_llm_response,
    merge_collected_data,
    get_missing_fields,
    format_confirm_message,
)
from .prompts import CHATBOT_SYSTEM_PROMPT, CHATBOT_USER_PROMPT

_KST = zoneinfo.ZoneInfo("Asia/Seoul")
_MAX_INPUT_LENGTH = 500


class ChatbotEngine:
    def __init__(self, post_id=None, auto_filled=None):
        self.post_id = post_id
        self.auto_filled = auto_filled or {}
        self.collected_data = {}
        self.provider = get_llm_provider()
        self.state = "COLLECTING"

        if auto_filled:
            self.collected_data = merge_collected_data(
                self.collected_data, {}, auto_filled
            )

    def _post_context_message(self) -> str:
        filled_info = []
        if "available_date" in self.auto_filled:
            filled_info.append(f"날짜: {self.auto_filled['available_date']}")
        if "max_animal_size" in self.auto_filled:
            filled_info.append(f"동물 크기: {self.auto_filled['max_animal_size']}")
        return (
            "공고 정보를 확인했어요!\n" + "\n".join(filled_info)
            + "\n\n출발지와 이동 조건을 자유롭게 알려주세요. 예: '광주에서 출발하고 차 있어요'"
        )

    def get_initial_message(self) -> dict:
        message = (
            self._post_context_message() if self.post_id and self.auto_filled
            else (
                "안녕하세요! 이동봉사 동선을 등록할게요.\n"
                "출발지, 목적지, 날짜, 차량 유무, 동물 크기를 "
                "자유롭게 알려주세요.\n\n"
                "예: '이번주 토요일 광주에서 서울 가는데 차 있고 소형만 가능해요'"
            )
        )
        return {"state": "COLLECTING", "message": message, "completed": False}

    def _invalid_input(self, message: str) -> dict:
        return {"state": self.state, "message": message, "completed": False, "error": "INVALID_INPUT"}

    def _validate_input(self, user_message: str) -> dict | None:
        if not user_message or not user_message.strip():
            return self._invalid_input("메시지를 입력해주세요.")
        if len(user_message) > _MAX_INPUT_LENGTH:
            return self._invalid_input(f"입력이 너무 깁니다. {_MAX_INPUT_LENGTH}자 이내로 입력해주세요.")
        return None

    async def _call_llm(self, prompt: str) -> dict | None:
        llm_response = await self.provider.complete(prompt=prompt, system_prompt="")
        return parse_llm_response(llm_response)

    def _build_collecting_result(self, parsed: dict) -> dict:
        self.collected_data = merge_collected_data(
            self.collected_data, parsed.get("extracted", {}), self.auto_filled,
        )
        missing = get_missing_fields(self.collected_data)
        if not missing:
            self.state = "CONFIRMING"
            confirm_msg = format_confirm_message(self.collected_data)
            return {
                "state": "CONFIRMING", "message": confirm_msg + "\n\n[등록하기] [수정하기]",
                "input_type": "buttons", "options": ["등록하기", "수정하기"],
                "collected_data": self.collected_data, "completed": False,
            }
        next_question = parsed.get("next_question") or self._fallback_question(missing)
        return {
            "state": "COLLECTING", "message": next_question,
            "collected_data": self.collected_data, "missing_fields": missing, "completed": False,
        }

    async def process_input(self, user_message: str) -> dict:
        error = self._validate_input(user_message)
        if error:
            return error
        if self.state == "CONFIRMING":
            return self._handle_confirm(user_message)
        prev_state, prev_collected = self.state, {**self.collected_data}
        try:
            parsed = await self._call_llm(self._build_prompt(user_message))
            if parsed is None:
                return {"state": "COLLECTING", "message": "이해하지 못했어요. 다시 한번 말씀해주세요.",
                        "completed": False, "error": "PARSE_FAILED"}
            return self._build_collecting_result(parsed)
        except Exception:
            self.state, self.collected_data = prev_state, prev_collected
            return {"state": self.state, "message": "처리 중 오류가 발생했어요. 다시 시도해주세요.",
                    "completed": False, "error": "LLM_ERROR"}

    def _reset_collecting(self) -> dict:
        self.state = "COLLECTING"
        self.collected_data = {}
        if self.auto_filled:
            self.collected_data = merge_collected_data({}, {}, self.auto_filled)
        return self.get_initial_message()

    def _handle_confirm(self, user_message: str) -> dict:
        if user_message in ["등록하기", "네", "확인"]:
            self.state = "COMPLETED"
            return {"state": "COMPLETED", "message": "동선 등록이 완료되었습니다!",
                    "completed": True, "schedule_data": self._get_schedule_data()}
        if user_message in ["수정하기", "다시", "처음부터 다시"]:
            return self._reset_collecting()
        self.state = "COLLECTING"
        return {"state": "COLLECTING", "message": "수정하고 싶은 내용을 말씀해주세요.", "completed": False}

    def _build_prompt(self, user_message: str) -> str:
        today = datetime.now(tz=_KST).date().isoformat()
        system = CHATBOT_SYSTEM_PROMPT.replace("{today}", today)
        user = CHATBOT_USER_PROMPT.format(
            collected_data=json.dumps(self.collected_data, ensure_ascii=False),
            auto_filled=json.dumps(self.auto_filled, ensure_ascii=False),
            user_message=user_message,
        )
        return system + "\n\n" + user

    def _fallback_question(self, missing: list) -> str:
        fallback = {
            "origin": "어느 지역에서 출발하시나요?",
            "destination": "어디까지 이동하실 수 있나요?",
            "available_date": "이동 가능한 날짜가 언제인가요?",
            "vehicle_available": "차량이 있으신가요?",
            "max_animal_size": "탑승 가능한 동물 크기는 어떻게 되나요? (소형/중형/대형)",
        }
        return fallback.get(missing[0], "추가 정보를 알려주세요.")

    def _get_schedule_data(self) -> dict:
        data = {**self.collected_data}
        if self.post_id:
            data["post_id"] = self.post_id
        return data
