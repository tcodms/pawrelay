from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.volunteer import AppliedPostInfo, ScheduleCreateRequest, ScheduleCreateResponse, ScheduleItem, ScheduleListResponse
from app.repositories import volunteer_repo
from app.services import volunteer_service

router = APIRouter()


@router.get("/schedules", response_model=ScheduleListResponse)
async def get_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    schedules = await volunteer_repo.get_schedules_by_volunteer(db, current_user.id)
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


@router.post("/schedules", response_model=ScheduleCreateResponse)
async def create_schedule(
    body: ScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await volunteer_service.create_schedule(db, current_user.id, body)
