from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.services import ws_service
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    share_token: str | None = None,
) -> None:
    if share_token:
        await _handle_share_connection(ws, share_token)
    else:
        await _handle_user_connection(ws)


async def _handle_share_connection(ws: WebSocket, share_token: str) -> None:
    async with AsyncSessionLocal() as db:
        if not await ws_service.is_valid_share_token(db, share_token):
            await ws.close(code=4004)
            return

    await manager.connect_share(ws, share_token)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_share(ws, share_token)


async def _handle_user_connection(ws: WebSocket) -> None:
    token = ws.cookies.get("access_token")
    user_id = decode_access_token(token) if token else None
    if not user_id:
        await ws.close(code=4001)
        return

    await manager.connect_user(ws, user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_user(ws, user_id)
