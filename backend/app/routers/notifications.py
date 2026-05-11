from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.dependencies import get_current_user, get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationItem, UnreadNotificationsResponse

router = APIRouter()


@router.get("/unread", response_model=UnreadNotificationsResponse)
async def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.channel == "in_app",
            Notification.read_at.is_(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifications = result.scalars().all()
    return UnreadNotificationsResponse(
        notifications=[_to_item(n) for n in notifications]
    )


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail={"error": "NOTIFICATION_NOT_FOUND"})
    if notification.read_at is None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read_at=func.now())
        )
        await db.commit()
    return {"ok": True}


def _to_item(n: Notification) -> NotificationItem:
    payload = n.payload or {}
    return NotificationItem(
        id=n.id,
        type=n.type,
        title=payload.get("title"),
        body=payload.get("body"),
        message=payload.get("message"),
        payload=payload,
        is_read=n.read_at is not None,
        created_at=n.created_at,
    )
