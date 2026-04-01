import json
from .base import LLMProvider


class MockProvider(LLMProvider):
    """테스트용 Mock Provider. API 키 없이 동작한다."""

    async def complete(self, prompt: str) -> str:
        return json.dumps({
            "chain": [
                {
                    "volunteer_id": 1,
                    "segment": "광주 → 천안",
                    "handover_time": "14:30"
                },
                {
                    "volunteer_id": 2,
                    "segment": "천안 → 서울",
                    "handover_time": "16:00"
                }
            ],
            "backup_candidates": {"segment_2": [5, 7]},
            "matching_reason": "[Mock] 두 봉사자의 동선이 천안에서 자연스럽게 이어지는 테스트 응답입니다."
        }, ensure_ascii=False)
