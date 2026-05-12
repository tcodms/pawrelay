from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_id, get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationItem, UnreadNotificationsResponse
from app.schemas.push import PushSubscribeIn, VapidKeyOut
from app.services import notification_service, push_service

router = APIRouter()


@router.get("/unread", response_model=UnreadNotificationsResponse)
async def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications = await notification_service.get_unread_for_user(db, current_user.id)
    return UnreadNotificationsResponse(
        notifications=[_to_item(n) for n in notifications]
    )


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.mark_as_read(db, notification_id, current_user.id)
    return {"ok": True}


@router.get("/push/vapid-key", response_model=VapidKeyOut)
def get_vapid_key():
    return VapidKeyOut(public_key=push_service.get_vapid_public_key())


@router.post("/push/subscribe")
async def push_subscribe(
    body: PushSubscribeIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await push_service.subscribe(db, user_id, body)
    return {"ok": True}


@router.delete("/push/subscribe")
async def push_unsubscribe(
    body: PushSubscribeIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await push_service.unsubscribe(db, user_id, body.endpoint)
    return {"ok": True}


def _to_item(n: Notification) -> NotificationItem:
    return NotificationItem(
        id=n.id,
        type=n.type,
        title=n.title,
        body=n.body,
        message=n.message,
        payload=n.payload or {},
        is_read=n.read_at is not None,
        created_at=n.created_at,
    )
