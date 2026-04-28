from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import post_repo, user_repo
from app.schemas.shelter import AnimalInfo, DashboardPostItem, RelaySegmentItem, ShelterDashboardResponse, ShelterProfileResponse

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
    chain_ids = [chain_id for _, _, chain_id, _, _ in rows if chain_id]
    segments_by_chain = await post_repo.get_segments_for_chains(db, chain_ids)
    posts = [
        DashboardPostItem(
            id=post.id,
            origin=post.origin,
            destination=post.destination,
            scheduled_date=post.scheduled_date,
            status=post.status,
            volunteer_count=count,
            animal_info=AnimalInfo(
                name=post.animal_name,
                size=post.animal_size,
                photo_url=post.animal_photo_url,
            ),
            chain_id=chain_id,
            chain_expires_at=chain_expires_at,
            matching_reason=matching_reason,
            share_token=post.share_token,
            relay_segments=[
                RelaySegmentItem(**s) for s in segments_by_chain.get(chain_id, [])
            ] if chain_id else None,
        )
        for post, count, chain_id, matching_reason, chain_expires_at in rows
    ]
    return ShelterDashboardResponse(posts=posts)
