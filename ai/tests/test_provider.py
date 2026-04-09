import os

import pytest

from ai.providers import get_llm_provider


@pytest.mark.asyncio
async def test_mock_provider_complete():
    """MockProvider가 정상 동작하는지 확인."""
    os.environ["LLM_PROVIDER"] = "mock"
    provider = get_llm_provider()
    result = await provider.complete("테스트 프롬프트")
    assert result is not None
    assert len(result) > 0


@pytest.mark.asyncio
async def test_mock_provider_with_system_prompt():
    """system_prompt 파라미터가 오류 없이 동작하는지 확인."""
    os.environ["LLM_PROVIDER"] = "mock"
    provider = get_llm_provider()
    result = await provider.complete(
        prompt="테스트 프롬프트",
        system_prompt="너는 테스트용 봇이야.",
    )
    assert result is not None


def test_invalid_provider_raises():
    """알 수 없는 LLM_PROVIDER는 ValueError를 발생시켜야 한다."""
    os.environ["LLM_PROVIDER"] = "unknown_provider"
    with pytest.raises(ValueError, match="알 수 없는 LLM_PROVIDER"):
        get_llm_provider()
    os.environ["LLM_PROVIDER"] = "mock"
