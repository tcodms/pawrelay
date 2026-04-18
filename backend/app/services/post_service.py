from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import post_repo
from app.schemas.post import (
    AnimalInfo,
    CheckpointItem,
    PostCreateResponse,
    PostDetailResponse,
    PostListResponse,
    PostPublicResponse,
    SegmentInfo,
    TimelineItem,
    PostListItem,
    VolunteerItem,
)


async def create_post(db: AsyncSession, shelter_id: int, data) -> PostCreateResponse:
    post = await post_repo.create_post(
        db=db,
        shelter_id=shelter_id,
        origin=data.origin,
        destination=data.destination,
        scheduled_date=data.scheduled_date,
        animal_name=data.animal_info.name,
        animal_size=data.animal_info.size,
        animal_photo_url=data.animal_info.photo_url,
        animal_notes=data.animal_info.notes,
    )
    return PostCreateResponse(id=post.id, share_token=post.share_token, status=post.status)


async def get_posts(
    db: AsyncSession,
    region: str | None,
    date_filter: date | None,
    animal_size: str | None,
    page: int,
    limit: int,
) -> PostListResponse:
    posts, total = await post_repo.get_posts(db, region, date_filter, animal_size, page, limit)
    items = [
        PostListItem(
            id=p.id,
            origin=p.origin,
            destination=p.destination,
            scheduled_date=p.scheduled_date,
            animal_size=p.animal_size,
            status=p.status,
            animal_photo_url=p.animal_photo_url,
        )
        for p in posts
    ]
    return PostListResponse(posts=items, total=total, page=page, limit=limit)


async def get_post_detail(db: AsyncSession, post_id: int, role: str | None) -> PostDetailResponse:
    post = await post_repo.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"error": "POST_NOT_FOUND"})
    animal_info = AnimalInfo(
        name=post.animal_name,
        size=post.animal_size,
        photo_url=post.animal_photo_url,
        notes=post.animal_notes,
    )
    if role == "shelter":
        rows = await post_repo.get_volunteers_for_post(db, post_id)
        volunteers = [
            VolunteerItem(id=r[0], name=r[1], from_area=r[2], to_area=r[3])
            for r in rows
        ]
        return PostDetailResponse(
            id=post.id, origin=post.origin, destination=post.destination,
            scheduled_date=post.scheduled_date, status=post.status,
            animal_info=animal_info, volunteers=volunteers,
        )
    count = await post_repo.count_volunteers_for_post(db, post_id)
    return PostDetailResponse(
        id=post.id, origin=post.origin, destination=post.destination,
        scheduled_date=post.scheduled_date, status=post.status,
        animal_info=animal_info, volunteer_count=count,
    )


async def update_post(db: AsyncSession, post_id: int, shelter_id: int, data) -> None:
    post = await post_repo.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"error": "POST_NOT_FOUND"})
    if post.shelter_id != shelter_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    if post.status != "recruiting":
        raise HTTPException(status_code=409, detail={"error": "POST_ALREADY_MATCHED"})

    animal_notes_provided = data.animal_info is not None
    notes = data.animal_info.notes if animal_notes_provided else None
    updated = await post_repo.update_post(
        db,
        post_id,
        scheduled_date=data.scheduled_date,
        animal_notes=notes,
        animal_notes_provided=animal_notes_provided,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"error": "POST_ALREADY_MATCHED"})


async def delete_post(db: AsyncSession, post_id: int, shelter_id: int) -> None:
    post = await post_repo.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"error": "POST_NOT_FOUND"})
    if post.shelter_id != shelter_id:
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    cancelled = await post_repo.cancel_post(db, post_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail={"error": "POST_ALREADY_MATCHED"})


async def get_public_post(db: AsyncSession, share_token: UUID) -> PostPublicResponse:
    post = await post_repo.get_post_by_share_token(db, share_token)
    if not post:
        raise HTTPException(status_code=404, detail={"error": "POST_NOT_FOUND"})

    current_segment, checkpoints, completed_segments = await post_repo.get_public_post_data(db, post)

    return PostPublicResponse(
        animal_info=AnimalInfo(
            name=post.animal_name,
            size=post.animal_size,
            photo_url=post.animal_photo_url,
            notes=post.animal_notes,
        ),
        origin=post.origin,
        destination=post.destination,
        scheduled_date=post.scheduled_date,
        current_segment=SegmentInfo(
            order=current_segment.segment_order,
            status=current_segment.status,
        ) if current_segment else None,
        checkpoints=[
            CheckpointItem(
                latitude=float(cp.latitude),
                longitude=float(cp.longitude),
                recorded_at=cp.recorded_at,
            )
            for cp in checkpoints
            if cp.latitude is not None and cp.longitude is not None
        ],
        timeline=[
            TimelineItem(
                segment_order=seg.segment_order,
                completed_at=seg.updated_at,
            )
            for seg in completed_segments
        ],
    )
