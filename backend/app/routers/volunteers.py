from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.volunteer import ScheduleCreateRequest, ScheduleCreateResponse, ScheduleListResponse
from app.services import volunteer_service

router = APIRouter()


@router.get("/schedules", response_model=ScheduleListResponse)
async def get_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await volunteer_service.list_schedules(db, current_user.id)


@router.post("/schedules", response_model=ScheduleCreateResponse)
async def create_schedule(
    body: ScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await volunteer_service.create_schedule(db, current_user.id, body)
