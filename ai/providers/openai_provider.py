import os
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    async def complete(self, prompt: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("OpenAI API 응답이 비어있습니다.")
        return response.choices[0].message.content