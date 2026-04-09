import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class VolunteerSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    activity_regions: list[str]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("WEAK_PASSWORD")
        return v


class ShelterSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    contact_email: EmailStr
    address: str
    shelter_registration_doc_url: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("WEAK_PASSWORD")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    model_config = {"from_attributes": True}


class SignupResponse(BaseModel):
    user: UserResponse


class LoginResponse(BaseModel):
    user: UserResponse
