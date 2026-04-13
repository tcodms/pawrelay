from datetime import date, datetime

from pydantic import BaseModel


class ShelterProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    verified_at: datetime | None


class DashboardPostItem(BaseModel):
    id: int
    origin: str
    destination: str
    scheduled_date: date
    status: str
    volunteer_count: int


class ShelterDashboardResponse(BaseModel):
    posts: list[DashboardPostItem]
