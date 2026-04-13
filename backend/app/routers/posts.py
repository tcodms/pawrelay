from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.post import (
    PostCreateRequest,
    PostCreateResponse,
    PostDetailResponse,
    PostListResponse,
    PostPublicResponse,
    PostUpdateRequest,
)
from app.services import post_service

router = APIRouter()


@router.get("", response_model=PostListResponse)
async def list_posts(
    region: str | None = Query(None),
    date: date | None = Query(None),
    animal_size: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await post_service.get_posts(db, region, date, animal_size, page, limit)


@router.post("", response_model=PostCreateResponse)
async def create_post(
    body: PostCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    return await post_service.create_post(db, current_user.id, body)


@router.get("/public/{share_token}", response_model=PostPublicResponse)
async def get_public_post(
    share_token: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await post_service.get_public_post(db, share_token)


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await post_service.get_post_detail(db, post_id)


@router.put("/{post_id}", response_model=dict)
async def update_post(
    post_id: int,
    body: PostUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    await post_service.update_post(db, post_id, current_user.id, body)
    return {"ok": True}


@router.delete("/{post_id}", response_model=dict)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "shelter":
        raise HTTPException(status_code=403, detail={"error": "UNAUTHORIZED"})
    await post_service.delete_post(db, post_id, current_user.id)
    return {"ok": True}
