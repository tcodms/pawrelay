from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class AnimalInfo(BaseModel):
    name: str
    size: str
    photo_url: str | None = None
    notes: str | None = None


class PostCreateRequest(BaseModel):
    origin: str
    destination: str
    scheduled_date: date
    animal_info: AnimalInfo


class AnimalInfoUpdate(BaseModel):
    notes: str | None = None


class PostUpdateRequest(BaseModel):
    scheduled_date: date | None = None
    animal_info: AnimalInfoUpdate | None = None


class PostCreateResponse(BaseModel):
    id: int
    share_token: UUID
    status: str


class PostListItem(BaseModel):
    id: int
    origin: str
    destination: str
    scheduled_date: date
    animal_size: str
    status: str
    animal_photo_url: str | None


class PostListResponse(BaseModel):
    posts: list[PostListItem]
    total: int
    page: int
    limit: int


class PostDetailResponse(BaseModel):
    id: int
    origin: str
    destination: str
    scheduled_date: date
    status: str
    animal_info: AnimalInfo


class CheckpointItem(BaseModel):
    latitude: float
    longitude: float
    recorded_at: datetime


class SegmentInfo(BaseModel):
    order: int
    status: str


class TimelineItem(BaseModel):
    segment_order: int
    completed_at: datetime


class PostPublicResponse(BaseModel):
    animal_info: AnimalInfo
    origin: str
    destination: str
    scheduled_date: date
    current_segment: SegmentInfo | None
    checkpoints: list[CheckpointItem]
    timeline: list[TimelineItem]
