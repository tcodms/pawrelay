import json

from .base import LLMProvider


class MockProvider(LLMProvider):
    """테스트용 Mock Provider. API 키 없이 동작한다.

    실제 LLM 없이도 챗봇 플로우를 순서대로 테스트할 수 있도록
    모든 필드를 null로 반환해 한 필드씩 질문하는 Multi-turn 흐름을 유지한다.
    """

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        return json.dumps({
            "extracted": {
                "origin": None,
                "destination": None,
                "available_date": None,
                "vehicle_available": None,
                "max_animal_size": None,
                "available_time": None,
                "estimated_arrival_time": None,
                "waypoint": None,
            },
            "next_question": None,
            "all_complete": False,
        }, ensure_ascii=False)
