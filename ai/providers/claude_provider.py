import asyncio
import os

from .base import LLMProvider


class ClaudeProvider(LLMProvider):
    def __init__(self):
        import anthropic

        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-sonnet-4-6"
        self._max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        # 클라이언트를 __init__에서 한 번만 생성해 재사용
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        kwargs = dict(
            model=self.model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        for attempt in range(3):
            try:
                async with asyncio.timeout(30):
                    response = await self.client.messages.create(**kwargs)
                if not response.content or not response.content[0].text:
                    raise ValueError("Claude API 응답이 비어있습니다.")
                return response.content[0].text
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
