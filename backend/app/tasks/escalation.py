import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.repositories import post_repo
from app.services import ws_service
from app.services.email_service import send_notification_email

logger = logging.getLogger(__name__)


async def escalate_d3() -> None:
    """D-3: 미매칭 공고 보호소에 WebSocket 알림"""
    async with AsyncSessionLocal() as db:
        posts = await post_repo.get_recruiting_posts_by_days_until(db, days=3)
        for post in posts:
            await ws_service.publish_user_event(
                redis_client, post.shelter_id, "escalation.d3",
                {"post_id": post.id, "scheduled_date": str(post.scheduled_date)},
            )
        logger.info("[에스컬레이션 D-3] %d건 처리", len(posts))


async def escalate_d2() -> None:
    """D-2: 미매칭 공고 보호소 WebSocket + 관리자 이메일 알림"""
    async with AsyncSessionLocal() as db:
        posts = await post_repo.get_recruiting_posts_by_days_until(db, days=2)
        for post in posts:
            await ws_service.publish_user_event(
                redis_client, post.shelter_id, "escalation.d2",
                {"post_id": post.id, "scheduled_date": str(post.scheduled_date)},
            )
        if posts:
            post_ids = ", ".join(str(p.id) for p in posts)
            await send_notification_email(
                settings.admin_email,
                f"[PawRelay D-2 알림] 미매칭 공고 {len(posts)}건 (ID: {post_ids}) — 출발 2일 전입니다.",
            )
        logger.info("[에스컬레이션 D-2] %d건 처리", len(posts))


async def escalate_d1() -> None:
    """D-1: 미매칭 공고 관리자 긴급 이메일 알림"""
    async with AsyncSessionLocal() as db:
        posts = await post_repo.get_recruiting_posts_by_days_until(db, days=1)
        if posts:
            post_ids = ", ".join(str(p.id) for p in posts)
            await send_notification_email(
                settings.admin_email,
                f"[PawRelay D-1 긴급] 미매칭 공고 {len(posts)}건 (ID: {post_ids}) — 내일 출발 예정입니다. 즉시 확인 바랍니다.",
            )
        logger.info("[에스컬레이션 D-1] %d건 처리", len(posts))
