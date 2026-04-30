from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import volunteer_repo
from app.schemas.volunteer import AppliedPostInfo, ScheduleCreateRequest, ScheduleCreateResponse, ScheduleItem, ScheduleListResponse
from app.services.geocoding_service import geocode


async def list_schedules(db: AsyncSession, volunteer_id: int) -> ScheduleListResponse:
    schedules = await volunteer_repo.get_schedules_by_volunteer(db, volunteer_id)
    items = []
    for s in schedules:
        applied_post = None
        if s.post:
            applied_post = AppliedPostInfo(
                animal_name=s.post.animal_name,
                animal_size=s.post.animal_size,
                animal_photo_url=s.post.animal_photo_url,
                origin=s.post.origin,
                destination=s.post.destination,
                post_status=s.post.status,
            )
        items.append(ScheduleItem(
            id=s.id,
            post_id=s.post_id,
            origin_area=s.origin_area,
            destination_area=s.destination_area,
            available_date=s.available_date,
            available_time=s.available_time,
            estimated_arrival_time=s.estimated_arrival_time,
            vehicle_available=s.vehicle_available,
            max_animal_size=s.max_animal_size,
            status=s.status,
            applied_post=applied_post,
        ))
    return ScheduleListResponse(schedules=items)


async def create_schedule(
    db: AsyncSession,
    volunteer_id: int,
    data: ScheduleCreateRequest,
) -> ScheduleCreateResponse:
    try:
        origin_lat, origin_lng = await geocode(data.origin)
        dest_lat, dest_lng = await geocode(data.destination)
    except ValueError as err:
        raise HTTPException(status_code=400, detail={"error": "GEOCODING_FAILED"}) from err

    route_wkt = (
        f"SRID=4326;LINESTRING({origin_lng} {origin_lat}, {dest_lng} {dest_lat})"
    )

    schedule = await volunteer_repo.create_schedule(
        db=db,
        volunteer_id=volunteer_id,
        post_id=data.post_id,
        route_description=data.route_description,
        origin_area=data.origin,
        destination_area=data.destination,
        available_date=data.available_date,
        available_time=data.available_time,
        estimated_arrival_time=data.estimated_arrival_time,
        vehicle_available=data.vehicle_available,
        max_animal_size=data.max_animal_size,
        route_wkt=route_wkt,
    )
    return ScheduleCreateResponse(schedule_id=schedule.id, status=schedule.status)
