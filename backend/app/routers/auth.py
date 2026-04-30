from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

from app.core.dependencies import get_current_user, get_current_user_id, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ShelterSignupRequest,
    SignupResponse,
    UserResponse,
    VolunteerSignupRequest,
)
from app.services import auth_service

_400_ERRORS = {"EMAIL_ALREADY_EXISTS", "ACCOUNT_SUSPENDED", "EMAIL_NOT_VERIFIED", "INVALID_VERIFICATION_TOKEN"}
_401_ERRORS = {"INVALID_CREDENTIALS", "REFRESH_TOKEN_EXPIRED"}

router = APIRouter()


@router.post("/signup/volunteer", response_model=SignupResponse)
async def signup_volunteer(
    body: VolunteerSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.signup_volunteer(db, body)
    except ValueError as e:
        if str(e) in _400_ERRORS:
            raise HTTPException(status_code=400, detail={"error": str(e)}) from e
        raise
    return SignupResponse(user=UserResponse.model_validate(user))


@router.post("/signup/shelter", response_model=SignupResponse)
async def signup_shelter(
    body: ShelterSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.signup_shelter(db, body)
    except ValueError as e:
        if str(e) in _400_ERRORS:
            raise HTTPException(status_code=400, detail={"error": str(e)}) from e
        raise
    return SignupResponse(user=UserResponse.model_validate(user))


@router.get("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        await auth_service.verify_email(token, db)
    except ValueError:
        return RedirectResponse(f"{settings.frontend_url}/auth/verify-email?error=invalid")
    return RedirectResponse(f"{settings.frontend_url}/auth/verify-email?success=true")


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.login(db, body, response)
    except ValueError as e:
        if str(e) in _401_ERRORS:
            raise HTTPException(status_code=401, detail={"error": str(e)}) from e
        if str(e) in _400_ERRORS:
            raise HTTPException(status_code=400, detail={"error": str(e)}) from e
        raise
    return LoginResponse(user=UserResponse.model_validate(user))


@router.post("/logout")
async def logout(
    response: Response,
    user_id: int = Depends(get_current_user_id),
):
    await auth_service.logout(response, user_id)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        await auth_service.refresh(refresh_token, response, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail={"error": str(e)}) from e
    return {"ok": True}
