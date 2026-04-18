from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import and_, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule

# 동물 크기 우선순위 (숫자가 클수록 큰 동물)
ANIMAL_SIZE_RANK = case(
    (VolunteerSchedule.max_animal_size == "small", 1),
    (VolunteerSchedule.max_animal_size == "medium", 2),
    (VolunteerSchedule.max_animal_size == "large", 3),
    else_=0,
)

POST_SIZE_RANK = {
    "small": 1,
    "medium": 2,
    "large": 3,
}

# PostGIS ST_DWithin 거리 기준 (단위: 미터), 약 50km
ROUTE_DISTANCE_METERS = 50_000


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
    post_size_rank = POST_SIZE_RANK.get(post.animal_size, 0)

    origin_point = ST_SetSRID(ST_MakePoint(origin_lng, origin_lat), 4326)
    dest_point = ST_SetSRID(ST_MakePoint(dest_lng, dest_lat), 4326)

    result = await db.execute(
        select(VolunteerSchedule).where(
            and_(
                VolunteerSchedule.available_date == post.scheduled_date,
                VolunteerSchedule.status == "available",
                ANIMAL_SIZE_RANK >= post_size_rank,
                VolunteerSchedule.route.isnot(None),
                ST_DWithin(
                    VolunteerSchedule.route,
                    origin_point,
                    ROUTE_DISTANCE_METERS,
                )
                | ST_DWithin(
                    VolunteerSchedule.route,
                    dest_point,
                    ROUTE_DISTANCE_METERS,
                ),
            )
        )
    )
    return list(result.scalars().all())
