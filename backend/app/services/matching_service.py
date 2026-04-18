import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import matching_repo
from app.services.geocoding_service import geocode

logger = logging.getLogger(__name__)


async def run_stage1_filter(db: AsyncSession) -> dict:
    """1단계: 날짜·동물크기·PostGIS 경로 기반 후보 봉사자 필터링"""
    posts = await matching_repo.get_recruiting_posts(db)
    logger.info(f"[매칭 1단계] recruiting 공고 {len(posts)}건")

    results = []
    for post in posts:
        try:
            origin_lat, origin_lng = await geocode(post.origin)
            dest_lat, dest_lng = await geocode(post.destination)
        except ValueError:
            logger.warning(f"[매칭 1단계] 공고 {post.id} geocoding 실패, 스킵")
            continue

        candidates = await matching_repo.get_candidate_volunteers(
            db, post, origin_lat, origin_lng, dest_lat, dest_lng
        )
        logger.info(f"[매칭 1단계] 공고 {post.id} → 후보 봉사자 {len(candidates)}명")
        results.append({
            "post_id": post.id,
            "candidate_count": len(candidates),
            "candidate_ids": [c.id for c in candidates],
        })

    return {"posts_processed": len(results), "results": results}
