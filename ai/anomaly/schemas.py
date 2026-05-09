from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DecisionType = Literal[
    "shelter_recommend",
    "admin_alert",
    "no_show_candidate",
    "chain_break_candidate",
    "reematch_candidate",
]

EventType = Literal["sos", "needs_verify", "checkpoint_delay"]
CheckpointType = Literal["departure", "waypoint"]


class RecommendedShelter(BaseModel):
    name: str
    address: str
    phone: str | None = None


class SosEvent(BaseModel):
    segment_id: int
    volunteer_id: int
    latitude: float
    longitude: float
    activity_region: str


class NeedsVerifyEvent(BaseModel):
    segment_id: int
    chain_id: int
    volunteer_id: int
    volunteer_name: str
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    handover_code_given_at: datetime | None = None
    handover_code_received_at: datetime | None = None


class CheckpointDelayEvent(BaseModel):
    segment_id: int
    chain_id: int
    volunteer_id: int
    volunteer_name: str
    scheduled_time: datetime
    delay_minutes: int
    last_checkpoint_type: CheckpointType | None = None
    last_checkpoint_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None


class AiDecisionEvent(BaseModel):
    event_type: EventType
    segment_id: int
    chain_id: int | None = None
    volunteer_id: int
    decision: DecisionType
    reason: str = Field(min_length=1)
    recommended_shelters: list[RecommendedShelter] = Field(default_factory=list)
    detected_at: datetime
    version: int = 1
