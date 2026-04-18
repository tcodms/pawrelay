import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule
from app.repositories import matching_repo
from app.services.geocoding_service import geocode

# ai/ 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "ai"))
from ai.matching.chain_selector import select_chain

logger = logging.getLogger(__name__)

HANDOVER_BUFFER = timedelta(minutes=30)

# 이동 속도 추정 (직선 거리 기반 MVP 근사값)
# TODO: 추후 카카오 길찾기 API로 실제 이동 시간 계산으로 고도화 필요
VEHICLE_SPEED_MPS = 60 * 1000 / 3600    # 차량 60km/h → m/s
TRANSIT_SPEED_MPS = 100 * 1000 / 3600  # 대중교통 100km/h → m/s


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


def _estimate_arrival(vol: VolunteerSchedule, route_length_m: float) -> datetime | None:
    """출발 시간 + 이동 시간(직선 거리 기반)으로 예상 도착 시간 계산"""
    departure = _parse_time(vol.available_time)
    if not departure:
        return None
    speed = VEHICLE_SPEED_MPS if vol.vehicle_available else TRANSIT_SPEED_MPS
    travel_seconds = route_length_m / speed
    return departure + timedelta(seconds=travel_seconds)


def _has_time_buffer(
    vol_a: VolunteerSchedule, route_length_m_a: float,
    vol_b: VolunteerSchedule,
) -> bool:
    """A의 예상 도착 시간 + HANDOVER_BUFFER <= B의 출발 시간인지 확인
    시간 정보 없으면 통과 (MVP 한계 — 추후 카카오 길찾기 API로 고도화 필요)
    """
    estimated_arrival_a = _estimate_arrival(vol_a, route_length_m_a)
    departure_b = _parse_time(vol_b.available_time)
    if not estimated_arrival_a or not departure_b:
        return True
    return departure_b >= estimated_arrival_a + HANDOVER_BUFFER


def _can_connect(
    vol_a: VolunteerSchedule, route_length_m_a: float,
    vol_b: VolunteerSchedule,
) -> bool:
    """A의 도착지와 B의 출발지가 연결 가능하고 시간 버퍼를 만족하는지 확인"""
    return (
        _regions_overlap(vol_a.destination_area, vol_b.origin_area)
        and _has_time_buffer(vol_a, route_length_m_a, vol_b)
    )


def _build_chains(
    candidates: list[tuple[VolunteerSchedule, float]],
    post_origin: str,
    post_destination: str,
) -> list[list[VolunteerSchedule]]:
    """DFS로 유효한 릴레이 체인 조합 탐색"""
    valid_chains: list[list[VolunteerSchedule]] = []
    length_map = {vol.id: length for vol, length in candidates}
    vols = [vol for vol, _ in candidates]

    def dfs(chain: list[VolunteerSchedule], used: set[int]) -> None:
        last = chain[-1]
        if _regions_overlap(last.destination_area, post_destination):
            valid_chains.append(list(chain))

        for vol in vols:
            if vol.id in used:
                continue
            if _can_connect(last, length_map[last.id], vol):
                chain.append(vol)
                used.add(vol.id)
                dfs(chain, used)
                chain.pop()
                used.remove(vol.id)

    starters = [vol for vol in vols if _regions_overlap(vol.origin_area, post_origin)]
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

    if not chains:
        logger.info(f"[매칭] 공고 {post.id} → 유효 체인 없음")
        return {"post_id": post.id, "candidate_count": len(candidates), "chain_id": None}

    # 3단계: LLM 최적 체인 선택
    chains_for_llm = [
        [
            {
                "origin_area": v.origin_area,
                "destination_area": v.destination_area,
                "available_date": str(v.available_date),
                "vehicle_available": v.vehicle_available,
            }
            for v in chain
        ]
        for chain in chains
    ]
    post_for_llm = {
        "id": post.id,
        "origin": post.origin,
        "destination": post.destination,
        "scheduled_date": str(post.scheduled_date),
        "animal_info": post.animal_name,
    }

    try:
        llm_result = await select_chain(chains_for_llm, post_for_llm)
        selected_index = llm_result["selected_chain_index"]
        matching_reason = llm_result["matching_reason"]
    except ValueError as e:
        logger.error(f"[매칭 3단계] 공고 {post.id} LLM 실패, 스킵: {e}")
        return {"post_id": post.id, "candidate_count": len(candidates), "chain_id": None}

    logger.info(f"[매칭 3단계] 공고 {post.id} → 체인 {selected_index} 선택")

    primary = chains[selected_index]
    backups = [c for i, c in enumerate(chains) if i != selected_index]
    saved_chain = await matching_repo.save_relay_chain(
        db, post.id, primary, backups, post.scheduled_date, matching_reason
    )
    logger.info(f"[매칭] 공고 {post.id} → relay_chain {saved_chain.id} 저장 완료")

    return {
        "post_id": post.id,
        "candidate_count": len(candidates),
        "chain_id": saved_chain.id,
        "segments": len(primary),
        "backup_count": len(backups),
        "matching_reason": matching_reason,
    }
