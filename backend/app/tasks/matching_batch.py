import logging

from app.core.database import AsyncSessionLocal
from app.services.matching_service import run_matching

logger = logging.getLogger(__name__)


async def run_batch_matching() -> None:
    async with AsyncSessionLocal() as db:
        result = await run_matching(db)
        logger.info("[자정 배치] 완료: %s", result)
