from datetime import datetime

from geoalchemy2.functions import ST_DWithin, ST_EndPoint, ST_Length, ST_MakePoint, ST_SetSRID, ST_StartPoint
from sqlalchemy import and_, case, select
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
) -> list[tuple[VolunteerSchedule, float]]:
    """후보 봉사자 목록과 각 경로 길이(미터) 반환"""
    post_size_rank = POST_SIZE_RANK.get(post.animal_size, 0)

    origin_point = ST_SetSRID(ST_MakePoint(origin_lng, origin_lat), 4326)
    dest_point = ST_SetSRID(ST_MakePoint(dest_lng, dest_lat), 4326)

    # ST_Length(..., true): use_spheroid=True → 미터 단위 반환
    route_length = ST_Length(VolunteerSchedule.route, True).label("route_length_m")

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
        select(VolunteerSchedule, route_length).where(
            and_(
                VolunteerSchedule.available_date == post.scheduled_date,
                VolunteerSchedule.status == "available",
                _animal_size_rank_expr() >= post_size_rank,
                VolunteerSchedule.route.isnot(None),
                geo_filter,
            )
        )
    )
    return [(row.VolunteerSchedule, float(row.route_length_m)) for row in result]


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
          "origin": v.origin_area, "destination": v.destination_area}
         for v in chain]
        for chain in backup_chains
    ]

    chain = RelayChain(
        transport_post_id=post_id,
        backup_candidates=backup_data if backup_data else None,
        matching_reason=matching_reason,
        status="proposed",
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

    await db.commit()
    return chain


def _build_scheduled_time(scheduled_date, available_time: str | None) -> datetime:
    """날짜 + 시간 문자열(HH:MM)을 datetime으로 변환. 시간 없으면 00:00"""
    time_str = available_time or "00:00"
    return datetime.strptime(
        f"{scheduled_date} {time_str}", "%Y-%m-%d %H:%M"
    )
