from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.relay import CheckpointIn, CheckpointOut
from app.services import relay_service

router = APIRouter()


@router.post("/checkpoint", response_model=CheckpointOut)
async def post_checkpoint(
    body: CheckpointIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await relay_service.save_checkpoint(db, user_id, body)
