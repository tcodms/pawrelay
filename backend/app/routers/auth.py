from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.auth import ShelterSignupRequest, SignupResponse, UserResponse, VolunteerSignupRequest
from app.services import auth_service

router = APIRouter()


@router.post("/signup/volunteer", response_model=SignupResponse)
async def signup_volunteer(
    body: VolunteerSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.signup_volunteer(db, body, response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})
    return SignupResponse(user=UserResponse.model_validate(user))


@router.post("/signup/shelter", response_model=SignupResponse)
async def signup_shelter(
    body: ShelterSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.signup_shelter(db, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})
    return SignupResponse(user=UserResponse.model_validate(user))
