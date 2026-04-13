from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import post_repo, user_repo
from app.schemas.shelter import DashboardPostItem, ShelterDashboardResponse, ShelterProfileResponse

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


@router.get("/dashboard", response_model=ShelterDashboardResponse)
async def get_shelter_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    rows = await post_repo.get_dashboard_posts(db, current_user.id)
    posts = [
        DashboardPostItem(
            id=post.id,
            origin=post.origin,
            destination=post.destination,
            scheduled_date=post.scheduled_date,
            status=post.status,
            volunteer_count=count,
        )
        for post, count in rows
    ]
    return ShelterDashboardResponse(posts=posts)
