import uuid
import time
from typing import Optional
from .base import SessionManager


SESSION_TTL_SECONDS = 3600  # 1시간


class MockSessionManager(SessionManager):
    """메모리 기반 Mock 세션 매니저.

    Redis 연동 전 개발/테스트용.
    딕셔너리에 세션을 저장하고 TTL 1시간 만료를 처리한다.
    """

    def __init__(self):
        self._sessions = {}

    async def create(self, post_id: Optional[int] = None,
                     auto_filled: Optional[dict] = None) -> str:
        session_id = str(uuid.uuid4())

        self._sessions[session_id] = {
            "state": "ASK_ORIGIN",
            "collected_data": {},
            "auto_filled": auto_filled or {},
            "post_id": post_id,
            "created_at": time.time(),
        }

        return session_id

    async def get(self, session_id: str) -> Optional[dict]:
        session = self._sessions.get(session_id)

        if session is None:
            return None

        elapsed = time.time() - session["created_at"]
        if elapsed > SESSION_TTL_SECONDS:
            del self._sessions[session_id]
            return None

        return session

    async def update(self, session_id: str, data: dict) -> bool:
        session = await self.get(session_id)

        if session is None:
            return False

        session.update(data)
        self._sessions[session_id] = session
        return True

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False