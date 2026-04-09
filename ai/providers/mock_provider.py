import json

from .base import LLMProvider


class MockProvider(LLMProvider):
    """테스트용 Mock Provider. API 키 없이 동작한다."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        return json.dumps({
            "extracted": {
                "origin": "광주광역시",
                "destination": "서울특별시",
                "available_date": "2026-04-10",
                "vehicle_available": True,
                "max_animal_size": "small",
                "available_time": "14:00 ~ 16:00",
                "waypoint": None,
            },
            "next_question": None,
            "all_complete": True,
        }, ensure_ascii=False)
