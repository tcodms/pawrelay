from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.core.redis import redis_client
from app.schemas.relay import (
    CheckpointIn, CheckpointOut,
    DelayIn, DelayOut,
    HandoverApproveOut, HandoverLocationIn, HandoverLocationOut,
    HandoverRequestOut, HandoverVerifyIn, HandoverVerifyOut,
    SosIn, SosOut,
)
from app.services import relay_service

router = APIRouter()


@router.post("/checkpoint", response_model=CheckpointOut)
async def post_checkpoint(
    body: CheckpointIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.save_checkpoint(db, user_id, body)


@router.post("/handover/verify", response_model=HandoverVerifyOut)
async def verify_handover(
    request: Request,
    body: HandoverVerifyIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    return await relay_service.verify_handover(db, redis_client, user_id, client_ip, body)


@router.post("/handover/request/{segment_id}", response_model=HandoverRequestOut)
async def request_handover(
    segment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.request_handover(db, user_id, segment_id)


@router.post("/handover/approve/{segment_id}", response_model=HandoverApproveOut)
async def approve_handover(
    segment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.approve_handover(db, user_id, segment_id)


@router.patch("/segments/{segment_id}/handover-location", response_model=HandoverLocationOut)
async def update_handover_location(
    segment_id: int,
    body: HandoverLocationIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.update_handover_location(db, user_id, segment_id, body)


@router.post("/emergency/sos", response_model=SosOut)
async def emergency_sos(
    body: SosIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.report_sos(db, user_id, body)


@router.post("/emergency/delay", response_model=DelayOut)
async def emergency_delay(
    body: DelayIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.report_delay(db, user_id, body)
