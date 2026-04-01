from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLM API 추상화 베이스 클래스.

    모든 LLM Provider는 이 클래스를 상속받아
    complete() 메서드를 구현해야 한다.
    """

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """프롬프트를 받아 LLM 응답을 반환한다."""
        pass
