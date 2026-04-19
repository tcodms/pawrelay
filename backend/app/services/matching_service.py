import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule
from app.repositories import matching_repo
from app.services.geocoding_service import geocode

# ai/ 모듈 경로 추가 (프로젝트 루트: pawrelay/)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ai.matching.chain_selector import select_chain

logger = logging.getLogger(__name__)

HANDOVER_BUFFER = timedelta(minutes=30)

_SIDO_SUFFIXES = ("특별시", "광역시", "특별자치시", "특별자치도", "도")
_SIDO_MAP = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
    "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
    "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도",
    "강원": "강원도", "충북": "충청북도", "충남": "충청남도",
    "전북": "전라북도", "전남": "전라남도",
    "경북": "경상북도", "경남": "경상남도", "제주": "제주특별자치도",
}


def _normalize_sido(area: str | None) -> str:
    """시/도 단위로 정규화. 예: '광주광역시 북구' → '광주광역시'"""
    if not area:
        return ""
    for suffix in _SIDO_SUFFIXES:
        if suffix in area:
            return area[:area.index(suffix) + len(suffix)]
    for short, full in _SIDO_MAP.items():
        if area.startswith(short):
            return full
    return area


def _parse_time(time_str: str | None) -> datetime | None:
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return None


def _has_time_buffer(vol_a: VolunteerSchedule, vol_b: VolunteerSchedule) -> bool:
    """A의 도착 예정 시간 + HANDOVER_BUFFER <= B의 출발 시간인지 확인
    시간 정보 없으면 통과 (MVP 한계)
    """
    estimated_arrival_a = _parse_time(vol_a.estimated_arrival_time)
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


# ── approve / reject ──────────────────────────────────────────────────────────

async def approve_chain(db: AsyncSession, chain_id: int, volunteer_id: int) -> dict:
    from fastapi import HTTPException

    chain = await matching_repo.get_chain_by_id(db, chain_id, for_update=True)
    if not chain:
        raise HTTPException(status_code=404, detail={"error": "CHAIN_NOT_FOUND"})
    if chain.status != "proposed":
        raise HTTPException(status_code=400, detail={"error": "CHAIN_NOT_PROPOSED"})
    if volunteer_id not in [s.volunteer_id for s in chain.segments]:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    try:
        volunteer_ids = [s.volunteer_id for s in chain.segments]
        scheduled_date = chain.transport_post.scheduled_date if chain.transport_post else None
        await matching_repo.activate_chain(db, chain)
        await matching_repo.mark_schedules_matched(db, volunteer_ids, scheduled_date)

        conflicting = await matching_repo.get_proposed_chains_with_volunteers(
            db, volunteer_ids, exclude_chain_id=chain_id
        )
        for conflicted in conflicting:
            await matching_repo.cancel_chain(db, conflicted)
            promoted = await matching_repo.promote_backup(
                db, conflicted, conflicted.transport_post.scheduled_date if conflicted.transport_post else None
            )
            if not promoted:
                await matching_repo.restore_post_to_recruiting(db, conflicted.transport_post_id)

        await db.commit()
        return {"chain_id": chain_id, "status": "active", "cancelled_chains": len(conflicting)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[approve_chain] chain {chain_id} 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR"})


async def reject_chain(db: AsyncSession, chain_id: int, volunteer_id: int) -> dict:
    from fastapi import HTTPException

    chain = await matching_repo.get_chain_by_id(db, chain_id, for_update=True)
    if not chain:
        raise HTTPException(status_code=404, detail={"error": "CHAIN_NOT_FOUND"})
    if chain.status != "proposed":
        raise HTTPException(status_code=400, detail={"error": "CHAIN_NOT_PROPOSED"})
    if volunteer_id not in [s.volunteer_id for s in chain.segments]:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    try:
        await matching_repo.cancel_chain(db, chain)

        promoted = await matching_repo.promote_backup(
            db, chain, chain.transport_post.scheduled_date if chain.transport_post else None
        )
        if not promoted:
            await matching_repo.restore_post_to_recruiting(db, chain.transport_post_id)

        await db.commit()
        return {"chain_id": chain_id, "status": "broken", "promoted": promoted is not None}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[reject_chain] chain {chain_id} 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR"})


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
                "available_time": v.available_time,
                "estimated_arrival_time": v.estimated_arrival_time,
                "vehicle_available": v.vehicle_available,
                "max_animal_size": v.max_animal_size,
                "is_direct_apply": v.post_id == post.id,
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

    if not isinstance(selected_index, int) or not (0 <= selected_index < len(chains)):
        logger.error(f"[매칭 3단계] 공고 {post.id} 잘못된 체인 인덱스: {selected_index}")
        return {"post_id": post.id, "candidate_count": len(candidates), "chain_id": None}

    logger.info(f"[매칭 3단계] 공고 {post.id} → 체인 {selected_index} 선택")

    primary = chains[selected_index]
    backups = [c for i, c in enumerate(chains) if i != selected_index]
    saved_chain = await matching_repo.save_relay_chain(
        db, post.id, primary, backups, post.scheduled_date, matching_reason
    )
    await db.commit()
    logger.info(f"[매칭] 공고 {post.id} → relay_chain {saved_chain.id} 저장 완료")

    return {
        "post_id": post.id,
        "candidate_count": len(candidates),
        "chain_id": saved_chain.id,
        "segments": len(primary),
        "backup_count": len(backups),
        "matching_reason": matching_reason,
    }
