import asyncio
import copy
import time
import uuid
from typing import Optional

from ai.errors import SessionExpiredError
from .base import SessionManager


SESSION_TTL_SECONDS = 3600


class MockSessionManager(SessionManager):
    """인메모리 세션 관리자 (개발/테스트용).

    Note:
        프로덕션에서는 RedisSessionManager로 교체한다.
        asyncio.Lock으로 동시 접근 시 race condition을 방지한다.
    """

    def __init__(self):
        """인메모리 세션 저장소와 Lock을 초기화한다."""
        self._sessions: dict = {}
        self._lock = asyncio.Lock()

    async def create(self, post_id=None, auto_filled=None) -> str:
        """새 세션을 생성하고 session_id를 반환한다."""
        async with self._lock:
            session_id = str(uuid.uuid4())
            self._sessions[session_id] = {
                "state": "COLLECTING",
                "collected_data": {},
                "auto_filled": copy.deepcopy(auto_filled) if auto_filled else {},
                "post_id": post_id,
                "created_at": time.time(),
            }
            return session_id

    async def get(self, session_id: str) -> Optional[dict]:
        """세션을 조회한다. 만료 시 SessionExpiredError 발생."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if time.time() - session["created_at"] > SESSION_TTL_SECONDS:
                del self._sessions[session_id]
                raise SessionExpiredError()
            return copy.deepcopy(session)

    async def update(self, session_id: str, data: dict) -> bool:
        """세션 데이터를 갱신한다. 만료 시 SessionExpiredError 발생."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            if time.time() - session["created_at"] > SESSION_TTL_SECONDS:
                del self._sessions[session_id]
                raise SessionExpiredError()
            session.update(copy.deepcopy(data))
            return True

    async def delete(self, session_id: str) -> bool:
        """세션을 삭제한다. 삭제 성공 시 True 반환."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
