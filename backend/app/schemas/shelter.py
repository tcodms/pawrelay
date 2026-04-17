from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ShelterProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    verified_at: datetime | None


class AnimalInfo(BaseModel):
    name: str
    size: str
    photo_url: str | None


class DashboardPostItem(BaseModel):
    id: int
    origin: str
    destination: str
    scheduled_date: date
    status: str
    volunteer_count: int
    animal_info: AnimalInfo
    chain_id: int | None
    share_token: UUID


class ShelterDashboardResponse(BaseModel):
    posts: list[DashboardPostItem]
