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
    return await matching_service.run_matching(db)


@router.patch("/relay-chains/{chain_id}/approve")
async def approve_chain(
    chain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await matching_service.approve_chain(db, chain_id)


@router.patch("/relay-chains/{chain_id}/reject")
async def reject_chain(
    chain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await matching_service.reject_chain(db, chain_id)
