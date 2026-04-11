import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, field_validator

AnimalSize = Literal["small", "medium", "large"]

_PW_SPECIAL = r"[!@#$%^&*()_+\-=\[\]{};:'\"\\|,.<>/?]"


class _PasswordMixin(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if (
            len(v) < 8
            or not re.search(r"[A-Za-z]", v)
            or not re.search(r"\d", v)
            or not re.search(_PW_SPECIAL, v)
        ):
            raise ValueError("WEAK_PASSWORD")
        return v


class VolunteerSignupRequest(_PasswordMixin):
    email: EmailStr
    password: str
    name: str
    vehicle_available: bool
    max_animal_size: AnimalSize
    activity_regions: list[str]


class ShelterSignupRequest(_PasswordMixin):
    email: EmailStr
    password: str
    name: str
    phone: str
    contact_email: EmailStr
    address: str
    shelter_registration_doc_url: Optional[str] = None


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
