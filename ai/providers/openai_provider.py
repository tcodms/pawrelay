import asyncio
import os

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI GPT API 기반 LLM 프로바이더."""

    def __init__(self):
        """OpenAI 클라이언트를 초기화한다. API 키 없으면 ValueError 발생."""
        from openai import AsyncOpenAI

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        self._max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        # 클라이언트를 __init__에서 한 번만 생성해 재사용
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """OpenAI API로 텍스트 완성을 요청한다. 최대 3회 재시도."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(3):
            try:
                async with asyncio.timeout(30):
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=self._max_tokens,
                    )
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("OpenAI API 응답이 비어있습니다.")
                return response.choices[0].message.content
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
