import urllib.parse

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.tasks import (
    approval_reminder,
    checkpoint_delay,
    departure_ping,
    escalation,
    handover_timeout,
    matching_batch,
)

_redis = urllib.parse.urlparse(settings.redis_url)

_jobstores = {
    "default": RedisJobStore(
        host=_redis.hostname or "localhost",
        port=_redis.port or 6379,
        db=0,
    ),
    # SOS date-trigger 잡은 메모리 jobstore 사용 (단기 일회성)
    "memory": MemoryJobStore(),
}

scheduler = AsyncIOScheduler(timezone="Asia/Seoul", jobstores=_jobstores)


def setup_scheduler() -> AsyncIOScheduler:
    # ── 기존 잡 ──────────────────────────────────────────────
    scheduler.add_job(
        handover_timeout.mark_stale_handovers,
        trigger=IntervalTrigger(minutes=5),
        id="handover_timeout",
        replace_existing=True,
    )
    scheduler.add_job(
        checkpoint_delay.detect_checkpoint_delays,
        trigger=IntervalTrigger(minutes=5),
        id="checkpoint_delay",
        replace_existing=True,
    )

    # ── 자정 배치 매칭 ────────────────────────────────────────
    scheduler.add_job(
        matching_batch.run_batch_matching,
        trigger=CronTrigger(hour=0, minute=0, timezone="Asia/Seoul"),
        id="run_matching",
        replace_existing=True,
    )

    # ── 에스컬레이션 (매일 09:00 KST) ────────────────────────
    scheduler.add_job(
        escalation.escalate_d3,
        trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
        id="escalation_d3",
        replace_existing=True,
    )
    scheduler.add_job(
        escalation.escalate_d2,
        trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
        id="escalation_d2",
        replace_existing=True,
    )
    scheduler.add_job(
        escalation.escalate_d1,
        trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
        id="escalation_d1",
        replace_existing=True,
    )

    # ── 출발 2시간 전 핑 (10분 간격) ─────────────────────────
    scheduler.add_job(
        departure_ping.send_departure_pings,
        trigger=IntervalTrigger(minutes=10),
        id="departure_ping",
        replace_existing=True,
    )

    # ── 매칭 승인 12시간 리마인더 (1시간 간격) ────────────────
    scheduler.add_job(
        approval_reminder.send_approval_reminders,
        trigger=IntervalTrigger(hours=1),
        id="matching_approval_reminder",
        replace_existing=True,
    )

    return scheduler
