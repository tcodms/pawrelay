from typing import Literal

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    session_id: str | None = None
    post_id: int | None = None
    message: str | None = None


class ChatMessageResponse(BaseModel):
    session_id: str
    state: str
    message: str
    input_type: Literal["address_search", "date_picker", "buttons", "text"] | None = None
    options: list[str] | None = None
    auto_filled: dict | None = None
    completed: bool
    schedule_id: int | None = None


class ChatSessionResponse(BaseModel):
    session_id: str
    state: str
    collected_data: dict
    auto_filled: dict | None = None


class ChatSessionListItem(BaseModel):
    session_id: str
    title: str
    last_message: str
    state: str
    updated_at: str


class ChatSessionsResponse(BaseModel):
    sessions: list[ChatSessionListItem]
