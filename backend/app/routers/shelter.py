from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import user_repo
from app.schemas.shelter import ShelterProfileResponse

router = APIRouter()


@router.get("/me", response_model=ShelterProfileResponse)
async def get_shelter_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    profile = await user_repo.get_shelter_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail={"error": "PROFILE_NOT_FOUND"})
    return ShelterProfileResponse(
        id=profile.id,
        name=profile.name,
        email=profile.email,
        verified_at=profile.verified_at,
    )
