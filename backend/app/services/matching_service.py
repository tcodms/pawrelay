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

# 시/도 단위 이동 시간 룩업 테이블 (단위: 분)
# car: 고속도로 기준 평균, transit: KTX 기준 (무궁화/버스 이용 시 과소 추정 가능)
# TODO: 챗봇에서 transit_type(KTX/일반기차/버스) 수집 후 세분화 필요
_TRAVEL_TIME: dict[tuple[str, str], dict[str, int]] = {
    ("서울특별시", "인천광역시"):      {"car": 60,  "transit": 70},
    ("서울특별시", "경기도"):          {"car": 60,  "transit": 60},
    ("서울특별시", "강원도"):          {"car": 120, "transit": 90},
    ("서울특별시", "세종특별자치시"):  {"car": 110, "transit": 55},
    ("서울특별시", "대전광역시"):      {"car": 100, "transit": 50},
    ("서울특별시", "충청북도"):        {"car": 120, "transit": 60},
    ("서울특별시", "충청남도"):        {"car": 120, "transit": 70},
    ("서울특별시", "전라북도"):        {"car": 180, "transit": 80},
    ("서울특별시", "광주광역시"):      {"car": 210, "transit": 90},
    ("서울특별시", "전라남도"):        {"car": 230, "transit": 110},
    ("서울특별시", "대구광역시"):      {"car": 200, "transit": 100},
    ("서울특별시", "경상북도"):        {"car": 210, "transit": 110},
    ("서울특별시", "부산광역시"):      {"car": 270, "transit": 155},
    ("서울특별시", "울산광역시"):      {"car": 260, "transit": 140},
    ("서울특별시", "경상남도"):        {"car": 260, "transit": 150},
    ("서울특별시", "제주특별자치도"):  {"car": 480, "transit": 480},
    ("인천광역시", "경기도"):          {"car": 40,  "transit": 50},
    ("인천광역시", "대전광역시"):      {"car": 110, "transit": 60},
    ("인천광역시", "광주광역시"):      {"car": 220, "transit": 100},
    ("인천광역시", "부산광역시"):      {"car": 280, "transit": 165},
    ("경기도", "강원도"):              {"car": 90,  "transit": 80},
    ("경기도", "대전광역시"):          {"car": 110, "transit": 60},
    ("경기도", "충청북도"):            {"car": 100, "transit": 70},
    ("경기도", "충청남도"):            {"car": 110, "transit": 75},
    ("경기도", "전라북도"):            {"car": 180, "transit": 90},
    ("경기도", "광주광역시"):          {"car": 220, "transit": 100},
    ("경기도", "대구광역시"):          {"car": 210, "transit": 110},
    ("경기도", "부산광역시"):          {"car": 280, "transit": 165},
    ("대전광역시", "세종특별자치시"):  {"car": 20,  "transit": 15},
    ("대전광역시", "충청북도"):        {"car": 50,  "transit": 30},
    ("대전광역시", "충청남도"):        {"car": 50,  "transit": 40},
    ("대전광역시", "전라북도"):        {"car": 80,  "transit": 40},
    ("대전광역시", "광주광역시"):      {"car": 130, "transit": 55},
    ("대전광역시", "대구광역시"):      {"car": 110, "transit": 55},
    ("대전광역시", "부산광역시"):      {"car": 180, "transit": 110},
    ("광주광역시", "전라남도"):        {"car": 60,  "transit": 40},
    ("광주광역시", "전라북도"):        {"car": 70,  "transit": 40},
    ("광주광역시", "대구광역시"):      {"car": 150, "transit": 80},
    ("광주광역시", "부산광역시"):      {"car": 200, "transit": 110},
    ("대구광역시", "경상북도"):        {"car": 50,  "transit": 30},
    ("대구광역시", "부산광역시"):      {"car": 80,  "transit": 45},
    ("대구광역시", "울산광역시"):      {"car": 70,  "transit": 40},
    ("대구광역시", "경상남도"):        {"car": 90,  "transit": 50},
    ("부산광역시", "울산광역시"):      {"car": 60,  "transit": 35},
    ("부산광역시", "경상남도"):        {"car": 50,  "transit": 40},
    ("울산광역시", "경상남도"):        {"car": 60,  "transit": 45},
    ("전라북도", "전라남도"):          {"car": 80,  "transit": 50},
    ("충청북도", "충청남도"):          {"car": 70,  "transit": 50},
    ("충청북도", "경상북도"):          {"car": 90,  "transit": 60},
    ("강원도", "경상북도"):            {"car": 120, "transit": 90},
}

_SIDO_SUFFIXES = ("특별시", "광역시", "특별자치시", "특별자치도", "도")
_SIDO_MAP = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
    "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
    "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도",
    "강원": "강원도", "충북": "충청북도", "충남": "충청남도",
    "전북": "전라북도", "전남": "전라남도",
    "경북": "경상북도", "경남": "경상남도", "제주": "제주특별자치도",
}


def _normalize_sido(area: str) -> str:
    """시/도 단위로 정규화. 예: '광주광역시 북구' → '광주광역시'"""
    for suffix in _SIDO_SUFFIXES:
        if suffix in area:
            return area[:area.index(suffix) + len(suffix)]
    for short, full in _SIDO_MAP.items():
        if area.startswith(short):
            return full
    return area


def _get_travel_minutes(origin_sido: str, dest_sido: str, mode: str) -> int | None:
    """시/도 쌍의 이동 시간(분) 반환. 양방향 조회."""
    times = _TRAVEL_TIME.get((origin_sido, dest_sido)) or _TRAVEL_TIME.get((dest_sido, origin_sido))
    if not times:
        return None
    return times.get(mode)


def _parse_time(time_str: str | None) -> datetime | None:
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return None


def _estimate_arrival(vol: VolunteerSchedule) -> datetime | None:
    """출발 시간 + 시/도 단위 룩업 테이블 기반 이동 시간으로 예상 도착 시간 계산"""
    departure = _parse_time(vol.available_time)
    if not departure:
        return None
    origin_sido = _normalize_sido(vol.origin_area)
    dest_sido = _normalize_sido(vol.destination_area)
    mode = "car" if vol.vehicle_available else "transit"
    minutes = _get_travel_minutes(origin_sido, dest_sido, mode)
    if minutes is None:
        return None
    return departure + timedelta(minutes=minutes)


def _has_time_buffer(vol_a: VolunteerSchedule, vol_b: VolunteerSchedule) -> bool:
    """A의 예상 도착 시간 + HANDOVER_BUFFER <= B의 출발 시간인지 확인
    시간 정보 없으면 통과 (MVP 한계)
    """
    estimated_arrival_a = _estimate_arrival(vol_a)
    departure_b = _parse_time(vol_b.available_time)
    if not estimated_arrival_a or not departure_b:
        return True
    return departure_b >= estimated_arrival_a + HANDOVER_BUFFER


def _can_connect(vol_a: VolunteerSchedule, vol_b: VolunteerSchedule) -> bool:
    """A의 도착지와 B의 출발지가 연결 가능하고 시간 버퍼를 만족하는지 확인"""
    return (
        _normalize_sido(vol_a.destination_area) == _normalize_sido(vol_b.origin_area)
        and _has_time_buffer(vol_a, vol_b)
    )


def _build_chains(
    candidates: list[VolunteerSchedule],
    post_origin: str,
    post_destination: str,
) -> list[list[VolunteerSchedule]]:
    """DFS로 유효한 릴레이 체인 조합 탐색"""
    valid_chains: list[list[VolunteerSchedule]] = []
    post_origin_sido = _normalize_sido(post_origin)
    post_dest_sido = _normalize_sido(post_destination)

    def dfs(chain: list[VolunteerSchedule], used: set[int]) -> None:
        last = chain[-1]
        if _normalize_sido(last.destination_area) == post_dest_sido:
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

    starters = [v for v in candidates if _normalize_sido(v.origin_area) == post_origin_sido]
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
