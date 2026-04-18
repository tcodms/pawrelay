from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import matching_service

router = APIRouter()


@router.post("/run")
async def run_matching(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.run_stage1_filter(db)
