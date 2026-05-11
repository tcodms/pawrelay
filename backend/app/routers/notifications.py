from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationItem, UnreadNotificationsResponse
from app.services import notification_service

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
