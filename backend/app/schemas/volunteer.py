from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    post_id: int | None = None
    route_description: str
    origin: str
    destination: str
    available_date: date
    available_time: str | None = Field(
        default=None,
        pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$",
    )
    estimated_arrival_time: str | None = Field(
        default=None,
        pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$",
    )
    vehicle_available: bool
    max_animal_size: Literal["small", "medium", "large"]


class ScheduleCreateResponse(BaseModel):
    schedule_id: int
    status: str


class AppliedPostInfo(BaseModel):
    animal_name: str
    animal_size: str
    animal_photo_url: str | None
    origin: str
    destination: str
    post_status: str

    model_config = {"from_attributes": True}


class ScheduleItem(BaseModel):
    id: int
    post_id: int | None
    origin_area: str
    destination_area: str
    available_date: date
    available_time: str | None
    estimated_arrival_time: str | None
    vehicle_available: bool
    max_animal_size: str
    status: str
    applied_post: AppliedPostInfo | None = None

    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    schedules: list[ScheduleItem]
