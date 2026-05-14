from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import post_repo, relay_repo, user_repo
from app.schemas.shelter import (
    AnimalInfo, DashboardPostItem, LocationInfo,
    RelayDetailResponse, RelaySegmentDetail, RelaySegmentItem,
    ShelterDashboardResponse, ShelterProfileResponse,
)

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
    posts = await _build_dashboard_posts(db, rows)
    return ShelterDashboardResponse(posts=posts)


@router.get("/posts/{post_id}/relay", response_model=RelayDetailResponse)
async def get_relay_detail(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})

    post = await post_repo.get_post_by_id(db, post_id)
    if not post or post.shelter_id != current_user.id:
        raise HTTPException(status_code=404, detail={"error": "POST_NOT_FOUND"})

    chain = await relay_repo.get_active_chain_by_post_id(db, post_id)
    if not chain:
        raise HTTPException(status_code=404, detail={"error": "CHAIN_NOT_FOUND"})

    segments = await relay_repo.get_segments_with_volunteers(db, chain.id)
    return RelayDetailResponse(segments=[_build_segment_detail(s) for s in segments])


def _resolve_chain_status(
    post_status: str,
    chain_id: int | None,
    chain_expires_at: datetime | None,
    now: datetime,
) -> str | None:
    if post_status != "waiting" or chain_id is None:
        return None
    if chain_expires_at is None:
        return None
    if chain_expires_at < now:
        return "auto_approved"
    return "pending_shelter"


async def _build_dashboard_posts(db: AsyncSession, rows: list) -> list[DashboardPostItem]:
    chain_ids = [chain_id for _, _, chain_id, _, _ in rows if chain_id]
    segments_by_chain = await post_repo.get_segments_for_chains(db, chain_ids)
    now = datetime.now(timezone.utc)
    return [_build_dashboard_post_item(row, segments_by_chain, now) for row in rows]


def _build_dashboard_post_item(row: tuple, segments_by_chain: dict, now: datetime) -> DashboardPostItem:
    post, count, chain_id, matching_reason, chain_expires_at = row
    return DashboardPostItem(
        id=post.id,
        origin=post.origin,
        destination=post.destination,
        scheduled_date=post.scheduled_date,
        status=post.status,
        volunteer_count=count,
        animal_info=_build_animal_info(post),
        chain_id=chain_id,
        chain_expires_at=chain_expires_at,
        chain_status=_resolve_chain_status(post.status, chain_id, chain_expires_at, now),
        matching_reason=matching_reason,
        share_token=post.share_token,
        relay_segments=_build_relay_segment_items(chain_id, segments_by_chain),
    )


def _build_animal_info(post) -> AnimalInfo:
    return AnimalInfo(
        name=post.animal_name,
        size=post.animal_size,
        photo_url=post.animal_photo_url,
    )


def _build_relay_segment_items(
    chain_id: int | None,
    segments_by_chain: dict,
) -> list[RelaySegmentItem] | None:
    if chain_id is None:
        return None
    return [RelaySegmentItem(**segment) for segment in segments_by_chain.get(chain_id, [])]


def _build_segment_detail(segment) -> RelaySegmentDetail:
    ping_status = _resolve_ping_status(segment, datetime.now(timezone.utc))
    return RelaySegmentDetail(
        order=segment.segment_order,
        volunteer_name=segment.volunteer.name if segment.volunteer else "",
        pickup_location=LocationInfo(name=segment.pickup_location, address=segment.pickup_location),
        dropoff_location=LocationInfo(name=segment.dropoff_location, address=segment.dropoff_location),
        status=segment.status,
        ping_status=ping_status,
    )


def _resolve_ping_status(segment, now: datetime) -> str:
    if segment.ping_responded_at:
        return "confirmed"
    if segment.ping_sent_at:
        if _is_departure_no_response(segment, now):
            return "departure_no_response"
        if segment.status == "accepted":
            return "pending"
        return "handover_no_response"
    return "pending"


def _is_departure_no_response(segment, now: datetime) -> bool:
    if segment.status != "accepted":
        return False
    if segment.ping_sent_at is None or segment.ping_responded_at is not None:
        return False
    if segment.scheduled_time is None:
        return False
    return segment.scheduled_time <= now + timedelta(hours=1)
