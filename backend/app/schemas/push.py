from pydantic import AnyUrl, BaseModel, Field


class PushKeysIn(BaseModel):
    p256dh: str = Field(..., min_length=1)
    auth: str = Field(..., min_length=1)


class PushSubscribeIn(BaseModel):
    endpoint: AnyUrl
    keys: PushKeysIn


class PushEndpointIn(BaseModel):
    endpoint: AnyUrl


class VapidKeyOut(BaseModel):
    public_key: str
