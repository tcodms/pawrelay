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
    vehicle_available: bool
    max_animal_size: Literal["small", "medium", "large"]


class ScheduleCreateResponse(BaseModel):
    schedule_id: int
    status: str
