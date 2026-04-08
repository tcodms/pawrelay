import os
from .base import LLMProvider


def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "mock")
    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "mock":
        from .mock_provider import MockProvider
        return MockProvider()
    else:
        raise ValueError(f"알 수 없는 LLM_PROVIDER: {provider_name}")