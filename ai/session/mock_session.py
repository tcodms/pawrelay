import uuid
import time
import copy
from typing import Optional
from .base import SessionManager


SESSION_TTL_SECONDS = 3600


class MockSessionManager(SessionManager):
    def __init__(self):
        self._sessions = {}

    async def create(self, post_id=None, auto_filled=None) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "state": "ASK_ORIGIN",
            "collected_data": {},
            "auto_filled": copy.deepcopy(auto_filled) if auto_filled else {},
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
        return copy.deepcopy(session)

    async def update(self, session_id: str, data: dict) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        elapsed = time.time() - session["created_at"]
        if elapsed > SESSION_TTL_SECONDS:
            del self._sessions[session_id]
            return False
        session.update(copy.deepcopy(data))
        return True

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False