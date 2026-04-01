import os
from .base import LLMProvider
from .mock_provider import MockProvider


def get_llm_provider() -> LLMProvider:
    """환경변수 LLM_PROVIDER에 따라 Provider 인스턴스를 반환한다.

    LLM_PROVIDER 값:
        openai  -> OpenAIProvider (gpt-4o-mini)
        claude  -> ClaudeProvider (claude-sonnet-4-6)
        mock    -> MockProvider (테스트용, API 키 불필요)
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock")

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider_name == "claude":
        from .claude_provider import ClaudeProvider
        return ClaudeProvider()

    elif provider_name == "mock":
        return MockProvider()

    else:
        raise ValueError(f"알 수 없는 LLM_PROVIDER: {provider_name}")
