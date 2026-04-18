import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule
from app.repositories import matching_repo
from app.services.geocoding_service import geocode

logger = logging.getLogger(__name__)

HANDOVER_BUFFER = timedelta(minutes=30)


# ── 2단계 헬퍼 ────────────────────────────────────────────────────────────────

MIN_REGION_LENGTH = 2  # 너무 짧은 문자열의 오탐 방지 (예: "구" in "대구광역시")


def _regions_overlap(area_a: str, area_b: str) -> bool:
    """두 지역명이 포함 관계인지 확인 (예: '천안' in '천안아산역')"""
    if len(area_a) < MIN_REGION_LENGTH or len(area_b) < MIN_REGION_LENGTH:
        return False
    return area_a in area_b or area_b in area_a


def _parse_time(time_str: str | None) -> datetime | None:
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return None


def _has_time_buffer(vol_a: VolunteerSchedule, vol_b: VolunteerSchedule) -> bool:
    """A 이후 B가 30분 이상 여유 있는지 확인. 시간 정보 없으면 통과"""
    time_a = _parse_time(vol_a.available_time)
    time_b = _parse_time(vol_b.available_time)
    if not time_a or not time_b:
        return True
    return time_b >= time_a + HANDOVER_BUFFER


def _can_connect(vol_a: VolunteerSchedule, vol_b: VolunteerSchedule) -> bool:
    """A의 도착지와 B의 출발지가 연결 가능하고 시간 버퍼를 만족하는지 확인"""
    return (
        _regions_overlap(vol_a.destination_area, vol_b.origin_area)
        and _has_time_buffer(vol_a, vol_b)
    )


def _build_chains(
    candidates: list[VolunteerSchedule],
    post_origin: str,
    post_destination: str,
) -> list[list[VolunteerSchedule]]:
    """DFS로 유효한 릴레이 체인 조합 탐색"""
    valid_chains: list[list[VolunteerSchedule]] = []

    def dfs(chain: list[VolunteerSchedule], used: set[int]) -> None:
        last = chain[-1]
        if _regions_overlap(last.destination_area, post_destination):
            valid_chains.append(list(chain))

        for vol in candidates:
            if vol.id in used:
                continue
            if _can_connect(last, vol):
                chain.append(vol)
                used.add(vol.id)
                dfs(chain, used)
                chain.pop()
                used.remove(vol.id)

    starters = [
        v for v in candidates
        if _regions_overlap(v.origin_area, post_origin)
    ]
    for starter in starters:
        dfs([starter], {starter.id})

    return valid_chains


# ── 메인 실행 함수 ─────────────────────────────────────────────────────────────

async def run_matching(db: AsyncSession) -> dict:
    """1단계 SQL 필터링 → 2단계 체인 알고리즘"""
    posts = await matching_repo.get_recruiting_posts(db)
    logger.info(f"[매칭] recruiting 공고 {len(posts)}건")

    results = []
    for post in posts:
        post_result = await _process_post(db, post)
        if post_result:
            results.append(post_result)

    return {"posts_processed": len(results), "results": results}


async def _process_post(db: AsyncSession, post: TransportPost) -> dict | None:
    try:
        origin_lat, origin_lng = await geocode(post.origin)
        dest_lat, dest_lng = await geocode(post.destination)
    except ValueError:
        logger.warning(f"[매칭] 공고 {post.id} geocoding 실패, 스킵")
        return None

    candidates = await matching_repo.get_candidate_volunteers(
        db, post, origin_lat, origin_lng, dest_lat, dest_lng
    )
    logger.info(f"[매칭 1단계] 공고 {post.id} → 후보 {len(candidates)}명")

    chains = _build_chains(candidates, post.origin, post.destination)
    logger.info(f"[매칭 2단계] 공고 {post.id} → 유효 체인 {len(chains)}개")

    return {
        "post_id": post.id,
        "candidate_count": len(candidates),
        "chains": [
            [{"schedule_id": v.id, "volunteer_id": v.volunteer_id,
              "origin": v.origin_area, "destination": v.destination_area,
              "time": v.available_time}
             for v in chain]
            for chain in chains
        ],
    }
