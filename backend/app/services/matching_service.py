import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from geoalchemy2.shape import to_shape

from app.core.redis import redis_client
from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule
from app.repositories import matching_repo, relay_repo
from app.services import notification_service, ws_service
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

async def approve_chain(db: AsyncSession, chain_id: int, user_id: int, role: str) -> dict:
    from fastapi import HTTPException

    chain = await matching_repo.get_chain_by_id(db, chain_id, for_update=True)
    if not chain:
        raise HTTPException(status_code=404, detail={"error": "CHAIN_NOT_FOUND"})
    if chain.status not in ("proposed", "active"):
        raise HTTPException(status_code=400, detail={"error": "CHAIN_NOT_PROPOSED"})
    if role == "volunteer" and user_id not in [s.volunteer_id for s in chain.segments]:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    # 이미 active인 경우 idempotent 반환
    if chain.status == "active":
        await db.commit()
        return {"chain_id": chain_id, "status": "active", "cancelled_chains": 0}

    try:
        volunteer_ids = [s.volunteer_id for s in chain.segments]
        scheduled_date = chain.transport_post.scheduled_date if chain.transport_post else None
        post_id = chain.transport_post_id
        await matching_repo.activate_chain(db, chain)

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
        logger.error(f"[approve_chain] chain {chain_id} 처리 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR"}) from e


async def reject_chain(db: AsyncSession, chain_id: int, user_id: int, role: str) -> dict:
    from fastapi import HTTPException

    chain = await matching_repo.get_chain_by_id(db, chain_id, for_update=True)
    if not chain:
        raise HTTPException(status_code=404, detail={"error": "CHAIN_NOT_FOUND"})
    if chain.status != "proposed":
        raise HTTPException(status_code=400, detail={"error": "CHAIN_NOT_PROPOSED"})
    if role == "volunteer" and user_id not in [s.volunteer_id for s in chain.segments]:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    try:
        post_id = chain.transport_post_id
        vol_infos = _extract_volunteer_infos(chain.segments)
        await matching_repo.cancel_chain(db, chain)

        promoted = await matching_repo.promote_backup(
            db, chain, chain.transport_post.scheduled_date if chain.transport_post else None
        )
        if not promoted:
            await matching_repo.restore_post_to_recruiting(db, chain.transport_post_id)

        await db.commit()
        await _notify_volunteers_by_infos(db, vol_infos, post_id, "matching_cancelled", "매칭 취소",
                                          "배정된 이동봉사 구간이 취소되었습니다.", chain_id)
        return {"chain_id": chain_id, "status": "broken", "promoted": promoted is not None}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[reject_chain] chain {chain_id} 처리 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR"}) from e


# ── 봉사자 segment 조회 / 수락 / 거절 ───────────────────────────────────────────

async def get_my_segments(db: AsyncSession, volunteer_id: int) -> dict:
    segments = await matching_repo.get_segments_for_volunteer(db, volunteer_id)
    return {
        "segments": [
            {
                "segment_id": seg.id,
                "status": seg.status,
                "animal_name": seg.chain.transport_post.animal_name if seg.chain and seg.chain.transport_post else "",
                "animal_photo_url": seg.chain.transport_post.animal_photo_url if seg.chain and seg.chain.transport_post else None,
                "scheduled_date": seg.chain.transport_post.scheduled_date.isoformat() if seg.chain and seg.chain.transport_post else None,
                "pickup_location": seg.pickup_location,
                "dropoff_location": seg.dropoff_location,
                "depart_time": seg.scheduled_time.strftime("%H:%M") if seg.scheduled_time else None,
            }
            for seg in segments
        ]
    }


def _build_location(name: str, lat, lng) -> dict:
    return {
        "name": name,
        "address": name,
        "lat": float(lat) if lat is not None else None,
        "lng": float(lng) if lng is not None else None,
    }


def _build_waypoints_dict(waypoint_rows: list) -> dict:
    result: dict[str, list] = {}
    for waypoint, distance_m in waypoint_rows:
        pt = to_shape(waypoint.geom)
        entry = {
            "id": waypoint.id,
            "name": waypoint.name,
            "address": waypoint.address,
            "lat": pt.y,
            "lng": pt.x,
            "distance_km": round(distance_m / 1000, 2),
        }
        result.setdefault(waypoint.type, []).append(entry)
    return result


def _build_chain_segments(chain_segments: list, volunteer_id: int) -> list:
    return [
        {
            "volunteer": seg.volunteer.name if seg.volunteer else "",
            "from": seg.pickup_location,
            "to": seg.dropoff_location,
            "is_me": seg.volunteer_id == volunteer_id,
        }
        for seg in chain_segments
    ]


def _build_segment_response(segment, partner, chain, post, waypoint_rows, volunteer_id) -> dict:
    shelter = post.shelter if post else None
    chain_segments = sorted(chain.segments, key=lambda s: s.segment_order) if chain else []
    expires_at = (chain.created_at + timedelta(hours=24)).isoformat() if chain else None
    return {
        "segment": {
            "order": segment.segment_order,
            "status": segment.status,
            "animal_name": post.animal_name if post else "",
            "animal_photo_url": post.animal_photo_url if post else None,
            "animal_size": post.animal_size if post else "small",
            "scheduled_date": post.scheduled_date.isoformat() if post else None,
            "pickup_location": _build_location(segment.pickup_location, segment.pickup_lat, segment.pickup_lng),
            "dropoff_location": _build_location(segment.dropoff_location, segment.dropoff_lat, segment.dropoff_lng),
            "scheduled_time": segment.scheduled_time.isoformat() if segment.scheduled_time else None,
            "depart_time": segment.scheduled_time.strftime("%H:%M") if segment.scheduled_time else None,
            "estimated_arrival_time": segment.estimated_arrival.strftime("%H:%M") if segment.estimated_arrival else None,
            "handover_code": segment.handover_code,
            "matching_reason": chain.matching_reason if chain else None,
            "notified_at": chain.created_at.isoformat() if chain else None,
            "expires_at": expires_at,
            "partner": {"name": partner.volunteer.name if partner and partner.volunteer else ""},
            "shelter_phone": shelter.shelter_profile.phone if shelter and shelter.shelter_profile else None,
            "kakao_openchat_url": post.kakao_openchat_url if post else None,
            "waypoints": _build_waypoints_dict(waypoint_rows),
            "chain_segments": _build_chain_segments(chain_segments, volunteer_id),
        }
    }


async def get_segment(db: AsyncSession, segment_id: int, volunteer_id: int) -> dict:
    from fastapi import HTTPException

    segment = await matching_repo.get_segment_by_id(db, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != volunteer_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    partner = await matching_repo.get_partner_segment(db, segment)
    chain = segment.chain
    post = chain.transport_post if chain else None

    waypoint_rows = []
    if segment.pickup_lat and segment.pickup_lng:
        waypoint_rows = await matching_repo.get_waypoints_near(
            db, float(segment.pickup_lat), float(segment.pickup_lng)
        )

    return _build_segment_response(segment, partner, chain, post, waypoint_rows, volunteer_id)


async def accept_segment(db: AsyncSession, segment_id: int, volunteer_id: int) -> dict:
    from fastapi import HTTPException

    segment = await matching_repo.get_segment_by_id(db, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != volunteer_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    if segment.status != "pending":
        raise HTTPException(status_code=400, detail={"error": "SEGMENT_NOT_PENDING"})

    segment.status = "accepted"
    segment.accepted_at = datetime.now(tz=timezone.utc)
    chain = segment.chain
    scheduled_date = chain.transport_post.scheduled_date if chain and chain.transport_post else None
    await matching_repo.mark_schedules_matched(db, volunteer_id, scheduled_date, chain.transport_post_id)

    # 체인 내 전원 수락 시 post → in_transit
    all_accepted = all(s.status == "accepted" for s in chain.segments)
    if all_accepted:
        await matching_repo.update_post_status(db, chain.transport_post_id, "in_transit")

    shelter_id = chain.transport_post.shelter_id if chain.transport_post else None
    post_id = chain.transport_post_id
    volunteer_name = segment.volunteer.name if segment.volunteer else f"봉사자#{volunteer_id}"
    all_vol_infos = _extract_volunteer_infos(chain.segments) if all_accepted else []
    await db.commit()
    if shelter_id:
        await _notify_shelter_segment_accepted(shelter_id, segment.id, volunteer_name, segment.segment_order)
    if all_accepted and shelter_id:
        await _notify_matching_confirmed(db, shelter_id, chain.id, post_id, all_vol_infos)

    segment = await matching_repo.get_segment_by_id(db, segment_id)
    partner = await matching_repo.get_partner_segment(db, segment)
    post = segment.chain.transport_post if segment.chain else None
    waypoint_rows = []
    if segment.pickup_lat and segment.pickup_lng:
        waypoint_rows = await matching_repo.get_waypoints_near(
            db, float(segment.pickup_lat), float(segment.pickup_lng)
        )
    return _build_segment_response(segment, partner, segment.chain, post, waypoint_rows, volunteer_id)


async def decline_segment(db: AsyncSession, segment_id: int, volunteer_id: int, reason: str) -> dict:
    from fastapi import HTTPException

    segment = await matching_repo.get_segment_by_id(db, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail={"error": "SEGMENT_NOT_FOUND"})
    if segment.volunteer_id != volunteer_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    if segment.status != "pending":
        raise HTTPException(status_code=400, detail={"error": "SEGMENT_NOT_PENDING"})

    segment.status = "no_show"
    segment.declined_at = datetime.now(tz=timezone.utc)
    segment.decline_reason = reason

    chain = segment.chain
    try:
        shelter_id = chain.transport_post.shelter_id if chain.transport_post else None
        post_id = chain.transport_post_id
        await matching_repo.cancel_chain(db, chain)
        scheduled_date = chain.transport_post.scheduled_date if chain.transport_post else None
        promoted = await matching_repo.promote_backup(db, chain, scheduled_date)
        if not promoted:
            await matching_repo.restore_post_to_recruiting(db, chain.transport_post_id)
        await db.commit()
        if not promoted and shelter_id:
            await _notify_shelter_matching_failed(db, shelter_id, post_id)
            await db.commit()
        return {"status": "declined", "promoted": promoted is not None}
    except Exception as e:
        await db.rollback()
        logger.error(f"[decline_segment] segment {segment_id} 처리 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR"}) from e


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


async def _notify_volunteers_matching_proposed(db: AsyncSession, chain_id: int, post_id: int) -> None:
    segments = await relay_repo.get_segments_with_volunteers(db, chain_id)
    for seg in segments:
        if not seg.volunteer:
            continue
        vol = seg.volunteer
        await notification_service.send_push_and_save(
            db, vol.id, vol.email, post_id,
            "matching_proposed", "이동봉사 매칭 제안",
            "새 이동봉사 구간이 배정되었습니다. 수락 여부를 확인해주세요.",
            {"segment_id": seg.id, "chain_id": chain_id},
        )


async def _notify_matching_confirmed(
    db: AsyncSession,
    shelter_id: int,
    chain_id: int,
    post_id: int,
    vol_infos: list[dict],
) -> None:
    await ws_service.publish_user_event(redis_client, shelter_id, "matching.confirmed", {
        "chain_id": chain_id,
    })
    await _notify_volunteers_by_infos(
        db, vol_infos, post_id,
        "matching_confirmed", "이동봉사 매칭 확정",
        "이동봉사 매칭이 확정되었습니다.", chain_id,
    )


async def _notify_matching_proposed_to_shelter(shelter_id: int, post_id: int, animal_name: str) -> None:
    await ws_service.publish_user_event(redis_client, shelter_id, "matching.proposed", {
        "post_id": post_id,
        "animal_name": animal_name,
    })


def _extract_volunteer_infos(segments) -> list[dict]:
    return [
        {"user_id": seg.volunteer_id, "email": seg.volunteer.email, "segment_id": seg.id}
        for seg in segments
        if seg.volunteer
    ]


async def _notify_volunteers_by_infos(
    db: AsyncSession,
    vol_infos: list[dict],
    post_id: int | None,
    notif_type: str,
    title: str,
    body: str,
    chain_id: int,
) -> None:
    for info in vol_infos:
        await notification_service.send_push_and_save(
            db, info["user_id"], info["email"], post_id,
            notif_type, title, body,
            {"segment_id": info["segment_id"], "chain_id": chain_id},
        )


async def _notify_shelter_segment_accepted(
    shelter_id: int, segment_id: int, volunteer_name: str, segment_order: int
) -> None:
    await ws_service.publish_user_event(redis_client, shelter_id, "segment.accepted", {
        "segment_id": segment_id,
        "volunteer_name": volunteer_name,
        "segment_order": segment_order,
    })


async def _notify_shelter_matching_failed(db: AsyncSession, shelter_id: int, post_id: int) -> None:
    await notification_service.save_in_app(
        db, shelter_id, post_id,
        "matching_failed", "매칭 실패",
        "이동봉사 매칭에 실패했습니다. 공고가 재모집 상태로 전환됩니다.",
        {"post_id": post_id},
    )


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
    await matching_repo.update_post_status(db, post.id, "waiting")
    shelter_id, post_id, animal_name = post.shelter_id, post.id, post.animal_name
    await db.commit()
    logger.info(f"[매칭] 공고 {post_id} → relay_chain {saved_chain.id} 저장 완료")
    await _notify_matching_proposed_to_shelter(shelter_id, post_id, animal_name)
    await _notify_volunteers_matching_proposed(db, saved_chain.id, post_id)

    return {
        "post_id": post_id,
        "candidate_count": len(candidates),
        "chain_id": saved_chain.id,
        "segments": len(primary),
        "backup_count": len(backups),
        "matching_reason": matching_reason,
    }
