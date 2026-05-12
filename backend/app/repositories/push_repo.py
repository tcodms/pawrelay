from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import PushSubscription


async def upsert_subscription(
    db: AsyncSession, user_id: int, endpoint: str, p256dh: str, auth: str
) -> None:
    stmt = (
        pg_insert(PushSubscription)
        .values(user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth)
        .on_conflict_do_update(
            constraint="uq_push_subscriptions_user_endpoint",
            set_={"p256dh": p256dh, "auth": auth},
        )
    )
    await db.execute(stmt)
    await db.commit()


async def delete_subscription(db: AsyncSession, user_id: int, endpoint: str) -> None:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint,
        )
    )
    await db.commit()


async def get_subscriptions_for_user(
    db: AsyncSession, user_id: int
) -> list[PushSubscription]:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    return list(result.scalars().all())
