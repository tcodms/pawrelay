from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.repositories import relay_repo

_HANDOVER_TIMEOUT_MINUTES = 30


async def mark_stale_handovers() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_HANDOVER_TIMEOUT_MINUTES)
    async with AsyncSessionLocal() as db:
        updated = await relay_repo.mark_stale_handovers_as_needs_verification(db, cutoff)
        if updated:
            await db.commit()
