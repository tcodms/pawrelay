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


class RelaySegmentItem(BaseModel):
    volunteer_name: str
    from_area: str
    to_area: str
    depart_time: str | None


class DashboardPostItem(BaseModel):
    id: int
    origin: str
    destination: str
    scheduled_date: date
    status: str
    volunteer_count: int
    animal_info: AnimalInfo
    chain_id: int | None
    chain_expires_at: datetime | None
    chain_status: str | None
    matching_reason: str | None
    share_token: UUID
    relay_segments: list[RelaySegmentItem] | None = None


class ShelterDashboardResponse(BaseModel):
    posts: list[DashboardPostItem]


class LocationInfo(BaseModel):
    name: str
    address: str


class RelaySegmentDetail(BaseModel):
    order: int
    volunteer_name: str
    pickup_location: LocationInfo
    dropoff_location: LocationInfo
    status: str
    ping_status: str


class RelayDetailResponse(BaseModel):
    segments: list[RelaySegmentDetail]
