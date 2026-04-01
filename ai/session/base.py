from abc import ABC, abstractmethod
from typing import Optional


class SessionManager(ABC):
    """세션 관리 추상화 베이스 클래스.

    Redis 연동 전 MockSessionManager로 개발하고,
    나중에 RedisSessionManager로 교체한다.
    """

    @abstractmethod
    async def create(self, post_id: Optional[int] = None,
                     auto_filled: Optional[dict] = None) -> str:
        """새 세션을 생성하고 session_id를 반환한다."""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[dict]:
        """session_id로 세션 데이터를 조회한다.

        Returns:
            dict: {state, collected_data, auto_filled, post_id, created_at}
            None: 세션이 없거나 만료된 경우
        """
        pass

    @abstractmethod
    async def update(self, session_id: str, data: dict) -> bool:
        """세션 데이터를 업데이트한다."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """세션을 삭제한다."""
        pass