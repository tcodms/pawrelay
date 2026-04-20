from datetime import datetime, timedelta, timezone

from geoalchemy2.functions import ST_DWithin, ST_EndPoint, ST_Length, ST_MakePoint, ST_SetSRID, ST_StartPoint
from sqlalchemy import and_, case, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.relay import RelayChain, RelaySegment
from app.models.volunteer import VolunteerSchedule

POST_SIZE_RANK = {
    "small": 1,
    "medium": 2,
    "large": 3,
}

# PostGIS ST_DWithin 거리 기준 (단위: 미터), 약 50km
ROUTE_DISTANCE_METERS = 50_000


def _animal_size_rank_expr():
    """쿼리 내부에서 동물 크기 우선순위 표현식 생성"""
    return case(
        (VolunteerSchedule.max_animal_size == "small", 1),
        (VolunteerSchedule.max_animal_size == "medium", 2),
        (VolunteerSchedule.max_animal_size == "large", 3),
        else_=0,
    )


async def get_recruiting_posts(db: AsyncSession) -> list[TransportPost]:
    result = await db.execute(
        select(TransportPost).where(TransportPost.status == "recruiting")
    )
    return list(result.scalars().all())


async def get_candidate_volunteers(
    db: AsyncSession,
    post: TransportPost,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> list[VolunteerSchedule]:
    """후보 봉사자 목록과 각 경로 길이(미터) 반환"""
    post_size_rank = POST_SIZE_RANK.get(post.animal_size, 0)

    origin_point = ST_SetSRID(ST_MakePoint(origin_lng, origin_lat), 4326)
    dest_point = ST_SetSRID(ST_MakePoint(dest_lng, dest_lat), 4326)

    # 차량: 전체 경로 기준 (중간 어디서든 픽업 가능)
    # 대중교통: 출발·도착 포인트 기준만 (정차역만 픽업 가능)
    vehicle_geo_filter = ST_DWithin(
        VolunteerSchedule.route, origin_point, ROUTE_DISTANCE_METERS
    ) | ST_DWithin(
        VolunteerSchedule.route, dest_point, ROUTE_DISTANCE_METERS
    )
    transit_geo_filter = (
        ST_DWithin(ST_StartPoint(VolunteerSchedule.route), origin_point, ROUTE_DISTANCE_METERS)
        | ST_DWithin(ST_StartPoint(VolunteerSchedule.route), dest_point, ROUTE_DISTANCE_METERS)
        | ST_DWithin(ST_EndPoint(VolunteerSchedule.route), origin_point, ROUTE_DISTANCE_METERS)
        | ST_DWithin(ST_EndPoint(VolunteerSchedule.route), dest_point, ROUTE_DISTANCE_METERS)
    )
    geo_filter = case(
        (VolunteerSchedule.vehicle_available.is_(True), vehicle_geo_filter),
        else_=transit_geo_filter,
    )

    result = await db.execute(
        select(VolunteerSchedule).where(
            and_(
                VolunteerSchedule.available_date == post.scheduled_date,
                VolunteerSchedule.status == "available",
                _animal_size_rank_expr() >= post_size_rank,
                VolunteerSchedule.route.isnot(None),
                geo_filter,
            )
        )
    )
    return list(result.scalars().all())


async def save_relay_chain(
    db: AsyncSession,
    post_id: int,
    primary_chain: list[VolunteerSchedule],
    backup_chains: list[list[VolunteerSchedule]],
    scheduled_date,
    matching_reason: str | None = None,
) -> RelayChain:
    """최적 체인을 relay_chains + relay_segments에 저장"""
    backup_data = [
        [{"schedule_id": v.id, "volunteer_id": v.volunteer_id,
          "origin": v.origin_area, "destination": v.destination_area,
          "available_time": v.available_time}
         for v in chain]
        for chain in backup_chains
    ]

    chain = RelayChain(
        transport_post_id=post_id,
        backup_candidates=backup_data if backup_data else None,
        matching_reason=matching_reason,
        status="proposed",
        chain_expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
    )
    db.add(chain)
    await db.flush()  # chain.id 확보

    for order, vol in enumerate(primary_chain):
        scheduled_time = _build_scheduled_time(scheduled_date, vol.available_time)
        segment = RelaySegment(
            chain_id=chain.id,
            volunteer_id=vol.volunteer_id,
            segment_order=order,
            pickup_location=vol.origin_area,
            dropoff_location=vol.destination_area,
            scheduled_time=scheduled_time,
        )
        db.add(segment)

    await db.flush()
    return chain


def _build_scheduled_time(scheduled_date, available_time: str | None) -> datetime:
    """날짜 + 시간 문자열(HH:MM)을 datetime으로 변환. 시간 없으면 00:00"""
    time_str = available_time or "00:00"
    dt = datetime.strptime(f"{scheduled_date} {time_str}", "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=timezone.utc)


async def get_chain_by_id(
    db: AsyncSession, chain_id: int, for_update: bool = False
) -> RelayChain | None:
    stmt = (
        select(RelayChain)
        .where(RelayChain.id == chain_id)
        .options(
            selectinload(RelayChain.segments),
            selectinload(RelayChain.transport_post),
        )
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_proposed_chains_with_volunteers(
    db: AsyncSession, volunteer_ids: list[int], exclude_chain_id: int
) -> list[RelayChain]:
    """주어진 봉사자 중 한 명이라도 포함된 proposed 상태 chain 목록 반환 (exclude_chain_id 제외)"""
    result = await db.execute(
        select(RelayChain)
        .join(RelaySegment, RelaySegment.chain_id == RelayChain.id)
        .where(
            and_(
                RelayChain.status == "proposed",
                RelayChain.id != exclude_chain_id,
                RelaySegment.volunteer_id.in_(volunteer_ids),
            )
        )
        .options(
            selectinload(RelayChain.segments),
            selectinload(RelayChain.transport_post),
        )
        .distinct()
    )
    return list(result.scalars().all())


async def activate_chain(db: AsyncSession, chain: RelayChain) -> None:
    chain.status = "active"
    for segment in chain.segments:
        segment.status = "accepted"
    await db.flush()


async def mark_schedules_matched(
    db: AsyncSession, volunteer_ids: list[int], scheduled_date
) -> None:
    schedules = await db.execute(
        select(VolunteerSchedule).where(
            and_(
                VolunteerSchedule.volunteer_id.in_(volunteer_ids),
                VolunteerSchedule.status == "available",
                VolunteerSchedule.available_date == scheduled_date,
            )
        )
    )
    for schedule in schedules.scalars().all():
        schedule.status = "matched"
    await db.flush()


async def cancel_chain(db: AsyncSession, chain: RelayChain) -> None:
    chain.status = "broken"
    await db.flush()


async def restore_post_to_recruiting(db: AsyncSession, post_id: int) -> None:
    result = await db.execute(
        select(TransportPost).where(TransportPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if post:
        post.status = "recruiting"
        await db.flush()


async def promote_backup(
    db: AsyncSession, broken_chain: RelayChain, scheduled_date
) -> RelayChain | None:
    """backup_candidates의 첫 번째 체인을 새 proposed chain으로 생성. 없으면 None 반환."""
    backups = broken_chain.backup_candidates
    if not backups:
        return None
    first_backup = backups[0]
    remaining_backups = backups[1:] if len(backups) > 1 else None

    new_chain = RelayChain(
        transport_post_id=broken_chain.transport_post_id,
        backup_candidates=remaining_backups,
        matching_reason=broken_chain.matching_reason,
        status="proposed",
        chain_expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
    )
    db.add(new_chain)
    await db.flush()

    for order, vol_data in enumerate(first_backup):
        scheduled_time = _build_scheduled_time(
            scheduled_date, vol_data.get("available_time")
        )
        segment = RelaySegment(
            chain_id=new_chain.id,
            volunteer_id=vol_data["volunteer_id"],
            segment_order=order,
            pickup_location=vol_data["origin"],
            dropoff_location=vol_data["destination"],
            scheduled_time=scheduled_time,
        )
        db.add(segment)

    await db.flush()
    return new_chain
