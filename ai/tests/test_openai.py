"""
OpenAI 실제 API 통합 테스트.

기본 테스트 스위트에서는 제외된다 (pytest.ini: addopts = -m "not integration").
실행하려면: pytest -m integration
"""
import os

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openai_real_api():
    """실제 OpenAI API 호출 테스트. OPENAI_API_KEY 환경변수 필요."""
    from ai.providers.openai_provider import OpenAIProvider

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY가 설정되지 않았습니다.")

    os.environ["LLM_PROVIDER"] = "openai"
    provider = OpenAIProvider()
    result = await provider.complete("'안녕'이라고만 대답해.")
    assert result is not None
    assert len(result) > 0
