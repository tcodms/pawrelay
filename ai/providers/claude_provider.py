import os
from .base import LLMProvider


class ClaudeProvider(LLMProvider):
    """Claude claude-sonnet-4-6 Provider."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-sonnet-4-6"

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    async def complete(self, prompt: str) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
