from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks import handover_timeout

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def setup_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(
        handover_timeout.mark_stale_handovers,
        trigger=IntervalTrigger(minutes=5),
        id="handover_timeout",
        replace_existing=True,
    )
    return scheduler
