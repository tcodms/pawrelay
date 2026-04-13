import os

from .base import SessionManager
from .mock_session import MockSessionManager

__all__ = ["SessionManager", "MockSessionManager", "RedisSessionManager",
           "get_session_manager"]


def get_session_manager() -> SessionManager:
    """환경변수 SESSION_BACKEND에 따라 SessionManager 인스턴스를 반환한다.

    SESSION_BACKEND 값:
        redis  -> RedisSessionManager (프로덕션)
        mock   -> MockSessionManager (개발/테스트, 기본값)
    """
    backend = os.getenv("SESSION_BACKEND", "mock")

    if backend == "redis":
        from .redis_session import RedisSessionManager
        return RedisSessionManager()

    return MockSessionManager()
