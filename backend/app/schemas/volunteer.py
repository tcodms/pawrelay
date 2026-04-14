from datetime import date

from pydantic import BaseModel


class ScheduleCreateRequest(BaseModel):
    post_id: int | None = None
    route_description: str
    origin: str
    destination: str
    available_date: date
    available_time: str | None = None
    vehicle_available: bool
    max_animal_size: str


class ScheduleCreateResponse(BaseModel):
    schedule_id: int
    status: str
