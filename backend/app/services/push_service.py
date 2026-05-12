import asyncio
import functools
import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import push_repo
from app.schemas.push import PushSubscribeIn
from app.services import email_service

logger = logging.getLogger(__name__)


def get_vapid_public_key() -> str:
    return settings.vapid_public_key


async def subscribe(db: AsyncSession, user_id: int, body: PushSubscribeIn) -> None:
    await push_repo.upsert_subscription(
        db, user_id, str(body.endpoint), body.keys.p256dh, body.keys.auth
    )


async def unsubscribe(db: AsyncSession, user_id: int, endpoint: str) -> None:
    await push_repo.delete_subscription(db, user_id, endpoint)


async def send_push_or_email_fallback(
    db: AsyncSession, user_id: int, user_email: str, payload: dict
) -> None:
    subscriptions = await push_repo.get_subscriptions_for_user(db, user_id)
    if not subscriptions:
        await email_service.send_notification_email(
            user_email, payload.get("message", "새 알림이 있습니다.")
        )
        return

    results = await asyncio.gather(
        *[_send_web_push(sub, payload) for sub in subscriptions]
    )
    if not any(results):
        await email_service.send_notification_email(
            user_email, payload.get("message", "새 알림이 있습니다.")
        )


_WEB_PUSH_TIMEOUT = 10.0


async def _send_web_push(subscription, payload: dict) -> bool:
    loop = asyncio.get_running_loop()
    masked = _mask_endpoint(subscription.endpoint)
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                None,
                functools.partial(
                    webpush,
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                    },
                    data=json.dumps(payload, ensure_ascii=False),
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_email},
                ),
            ),
            timeout=_WEB_PUSH_TIMEOUT,
        )
        return True
    except Exception as e:
        logger.warning("Web Push 발송 실패 endpoint=%s: %s", masked, e)
        return False


def _mask_endpoint(endpoint: str) -> str:
    return endpoint[:30] + "..." if len(endpoint) > 30 else endpoint
