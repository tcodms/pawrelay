from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.redis import redis_client
from app.models.user import User
from app.schemas.chatbot import ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
from app.services import chatbot_service

router = APIRouter()


def _require_volunteer(current_user: User) -> User:
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return current_user


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_volunteer(current_user)
    return await chatbot_service.send_message(
        redis=redis_client,
        db=db,
        volunteer_id=current_user.id,
        session_id=body.session_id,
        post_id=body.post_id,
        message=body.message,
    )


@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    _require_volunteer(current_user)
    return await chatbot_service.get_session(redis=redis_client, session_id=session_id, volunteer_id=current_user.id)


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    _require_volunteer(current_user)
    await chatbot_service.delete_session(redis=redis_client, session_id=session_id, volunteer_id=current_user.id)
