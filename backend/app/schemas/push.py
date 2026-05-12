from pydantic import BaseModel


class PushKeysIn(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeIn(BaseModel):
    endpoint: str
    keys: PushKeysIn


class VapidKeyOut(BaseModel):
    public_key: str
