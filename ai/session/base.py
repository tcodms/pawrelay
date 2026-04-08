from abc import ABC, abstractmethod
from typing import Optional


class SessionManager(ABC):
    @abstractmethod
    async def create(self, post_id=None, auto_filled=None) -> str:
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def update(self, session_id: str, data: dict) -> bool:
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        pass