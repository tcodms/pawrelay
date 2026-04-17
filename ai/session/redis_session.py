import json
import os
import uuid
from typing import Optional

import redis.asyncio as aioredis

from ai.errors import SessionExpiredError
from .base import SessionManager

SESSION_TTL_SECONDS = 3600


class RedisSessionManager(SessionManager):
    """Redis 기반 세션 관리자 (프로덕션용).

    환경변수 REDIS_URL로 연결 설정.
    TTL은 Redis 서버에서 관리하므로 get()/update() 시
    키가 없으면 만료로 간주해 SessionExpiredError를 raise한다.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """Redis 클라이언트를 초기화한다. redis_url 없으면 환경변수 REDIS_URL 사용."""
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = aioredis.from_url(url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        """Redis 저장 키를 생성한다."""
        return f"session:{session_id}"

    async def create(self, post_id=None, auto_filled=None) -> str:
        """새 세션을 Redis에 저장하고 session_id를 반환한다."""
        session_id = str(uuid.uuid4())
        data = {
            "state": "COLLECTING",
            "collected_data": {},
            "auto_filled": auto_filled or {},
            "post_id": post_id,
        }
        await self._redis.setex(
            self._key(session_id),
            SESSION_TTL_SECONDS,
            json.dumps(data, ensure_ascii=False),
        )
        return session_id

    async def get(self, session_id: str) -> Optional[dict]:
        """세션을 조회한다. 키 없으면 SessionExpiredError 발생."""
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            raise SessionExpiredError()
        return json.loads(raw)

    async def update(self, session_id: str, data: dict) -> bool:
        """세션 데이터를 갱신하고 TTL을 갱신한다. 키 없으면 SessionExpiredError 발생."""
        key = self._key(session_id)
        raw = await self._redis.get(key)
        if raw is None:
            raise SessionExpiredError()
        session = json.loads(raw)
        session.update(data)
        # 업데이트 시 TTL 갱신
        await self._redis.setex(key, SESSION_TTL_SECONDS,
                                json.dumps(session, ensure_ascii=False))
        return True

    async def delete(self, session_id: str) -> bool:
        """세션을 삭제한다. 삭제 성공 시 True 반환."""
        result = await self._redis.delete(self._key(session_id))
        return result > 0

    async def close(self) -> None:
        """앱 종료 시 Redis 연결 해제."""
        await self._redis.aclose()
