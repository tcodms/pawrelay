from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    transport_post_id: int | None,
    notif_type: str,
    title: str,
    body: str,
    channel: str,
    payload: dict,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        transport_post_id=transport_post_id,
        type=notif_type,
        title=title,
        body=body,
        channel=channel,
        payload=payload,
        status="pending",
    )
    db.add(notif)
    await db.flush()
    return notif
