import os

from .base import LLMProvider

_VALID_PROVIDERS = {"openai", "claude", "mock"}


def get_llm_provider() -> LLMProvider:
    """환경변수 LLM_PROVIDER에 따라 Provider 인스턴스를 반환한다.

    LLM_PROVIDER 값:
        openai  -> OpenAIProvider (gpt-4o-mini)
        claude  -> ClaudeProvider (claude-sonnet-4-6)
        mock    -> MockProvider (테스트용, API 키 불필요)
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock")

    if provider_name not in _VALID_PROVIDERS:
        raise ValueError(
            f"알 수 없는 LLM_PROVIDER: '{provider_name}'. "
            f"허용 값: {_VALID_PROVIDERS}"
        )

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider_name == "claude":
        from .claude_provider import ClaudeProvider
        return ClaudeProvider()

    else:
        from .mock_provider import MockProvider
        return MockProvider()


def validate_llm_provider() -> None:
    """FastAPI 앱 시작 시 호출해 설정을 미리 검증한다."""
    get_llm_provider()
