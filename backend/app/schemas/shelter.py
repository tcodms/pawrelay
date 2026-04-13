from datetime import datetime

from pydantic import BaseModel


class ShelterProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    verified_at: datetime | None
