from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.notification import Notification
from app.repositories import notification_repo
from app.services import push_service


async def get_unread_for_user(db: AsyncSession, user_id: int) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == "in_app",
            Notification.read_at.is_(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def send_push_and_save(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    transport_post_id: int | None,
    notif_type: str,
    title: str,
    body: str,
    payload: dict,
) -> None:
    await notification_repo.create_notification(
        db, user_id, transport_post_id, notif_type, title, body, "push", payload
    )
    await db.commit()
    await push_service.send_push_or_email_fallback(
        db, user_id, user_email, {"title": title, "message": body, **payload}
    )


async def save_in_app(
    db: AsyncSession,
    user_id: int,
    transport_post_id: int | None,
    notif_type: str,
    title: str,
    body: str,
    payload: dict,
) -> None:
    await notification_repo.create_notification(
        db, user_id, transport_post_id, notif_type, title, body, "in_app", payload
    )


async def mark_as_read(db: AsyncSession, notification_id: int, user_id: int) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
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
