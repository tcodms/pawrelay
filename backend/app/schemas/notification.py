from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationItem(BaseModel):
    id: int
    type: str
    title: str | None
    body: str | None
    message: str | None
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime


class UnreadNotificationsResponse(BaseModel):
    notifications: list[NotificationItem]
