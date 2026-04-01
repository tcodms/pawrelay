import asyncio
import os
from ai.providers import get_llm_provider


async def test_mock_provider():
    """MockProvider가 정상 동작하는지 확인."""
    os.environ["LLM_PROVIDER"] = "mock"

    provider = get_llm_provider()
    result = await provider.complete("테스트 프롬프트")

    print("=== Mock Provider 테스트 ===")
    print(f"Provider: {provider.__class__.__name__}")
    print(f"응답:\n{result}")
    print("=== 성공 ===")


if __name__ == "__main__":
    asyncio.run(test_mock_provider())
