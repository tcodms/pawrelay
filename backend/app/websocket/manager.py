import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._user_sockets: dict[int, set[WebSocket]] = defaultdict(set)
        self._share_sockets: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect_user(self, ws: WebSocket, user_id: int) -> None:
        await ws.accept()
        self._user_sockets[user_id].add(ws)

    async def connect_share(self, ws: WebSocket, share_token: str) -> None:
        await ws.accept()
        self._share_sockets[share_token].add(ws)

    def disconnect_user(self, ws: WebSocket, user_id: int) -> None:
        self._user_sockets[user_id].discard(ws)
        if not self._user_sockets[user_id]:
            del self._user_sockets[user_id]

    def disconnect_share(self, ws: WebSocket, share_token: str) -> None:
        self._share_sockets[share_token].discard(ws)
        if not self._share_sockets[share_token]:
            del self._share_sockets[share_token]

    async def send_to_user(self, user_id: int, data: dict) -> None:
        text = json.dumps(data, ensure_ascii=False)
        for ws in list(self._user_sockets.get(user_id, set())):
            try:
                await ws.send_text(text)
            except Exception:
                self._user_sockets[user_id].discard(ws)
                if not self._user_sockets.get(user_id):
                    self._user_sockets.pop(user_id, None)

    async def send_to_share(self, share_token: str, data: dict) -> None:
        text = json.dumps(data, ensure_ascii=False)
        for ws in list(self._share_sockets.get(share_token, set())):
            try:
                await ws.send_text(text)
            except Exception:
                self._share_sockets[share_token].discard(ws)
                if not self._share_sockets.get(share_token):
                    self._share_sockets.pop(share_token, None)


manager = ConnectionManager()
