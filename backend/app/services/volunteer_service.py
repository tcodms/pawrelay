from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import volunteer_repo
from app.schemas.volunteer import ScheduleCreateRequest, ScheduleCreateResponse
from app.services.geocoding_service import geocode


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
        vehicle_available=data.vehicle_available,
        max_animal_size=data.max_animal_size,
        route_wkt=route_wkt,
    )
    return ScheduleCreateResponse(schedule_id=schedule.id, status=schedule.status)
