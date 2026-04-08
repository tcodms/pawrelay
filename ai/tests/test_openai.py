import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from ai.providers.openai_provider import OpenAIProvider


async def test_openai_call():
    print("=== OpenAI 실제 호출 테스트 ===")

    provider = OpenAIProvider()
    prompt = "한국어로 '안녕하세요'라고만 답해주세요."

    result = await provider.complete(prompt)
    print(f"응답: {result}")

    assert len(result) > 0
    print("=== OpenAI 호출 테스트 성공 ===")


if __name__ == "__main__":
    asyncio.run(test_openai_call())