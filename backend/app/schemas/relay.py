from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CheckpointIn(BaseModel):
    segment_id: int
    type: Literal["departure", "waypoint", "arrival"]
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def gps_must_be_pair(self) -> "CheckpointIn":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must both be provided or both be null")
        return self


class CheckpointOut(BaseModel):
    checkpoint_id: int
    recorded_at: datetime


class HandoverVerifyIn(BaseModel):
    segment_id: int
    code: str = Field(pattern=r"^\d{6}$")


class HandoverVerifyOut(BaseModel):
    status: Literal["completed", "waiting_partner"]
