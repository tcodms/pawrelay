from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import matching_service


class DeclineRequest(BaseModel):
    reason: str = ""

router = APIRouter()


@router.post("/run")
async def run_matching(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.run_matching(db)


@router.patch("/relay-chains/{chain_id}/approve")
async def approve_chain(
    chain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("volunteer", "shelter"):
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.approve_chain(db, chain_id, current_user.id, current_user.role)


@router.patch("/relay-chains/{chain_id}/reject")
async def reject_chain(
    chain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("volunteer", "shelter"):
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.reject_chain(db, chain_id, current_user.id, current_user.role)


@router.get("/segments/{segment_id}")
async def get_segment(
    segment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.get_segment(db, segment_id, current_user.id)


@router.post("/accept/{segment_id}")
async def accept_matching(
    segment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.accept_segment(db, segment_id, current_user.id)


@router.post("/decline/{segment_id}")
async def decline_matching(
    segment_id: int,
    body: DeclineRequest = DeclineRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "volunteer":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await matching_service.decline_segment(db, segment_id, current_user.id, body.reason)
