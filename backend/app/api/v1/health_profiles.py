import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_user_ownership, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.health_profile import (
    HealthProfileCreate,
    HealthProfileResponse,
    HealthProfileUpdate,
)
from app.services import health_profile_service, user_service

router = APIRouter(prefix="/health-profiles", tags=["health-profiles"])


@router.post(
    "",
    response_model=HealthProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Health Profile",
    description="Create a health profile for a specific user (1:1 relationship).",
)
def create_health_profile_endpoint(
    profile_in: HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HealthProfileResponse:
    ensure_user_ownership(current_user, profile_in.user_id)
    # 1. Verify user exists
    user = user_service.get_user_by_id(db, profile_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{profile_in.user_id}' does not exist.",
        )

    # 2. Verify user doesn't already have a profile
    existing = health_profile_service.get_profile_by_user_id(db, profile_in.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Health profile already exists for user '{profile_in.user_id}'. Use PUT to update.",
        )

    return health_profile_service.create_profile(db, profile_in)


@router.get(
    "/user/{user_id}",
    response_model=HealthProfileResponse,
    summary="Get Health Profile by User ID",
    description="Retrieve the health profile (including calculated BMI) for a specific user.",
)
def get_health_profile_by_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HealthProfileResponse:
    ensure_user_ownership(current_user, user_id)
    profile = health_profile_service.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Health profile not found for user '{user_id}'.",
        )
    return profile


@router.put(
    "/user/{user_id}",
    response_model=HealthProfileResponse,
    summary="Update Health Profile",
    description="Update health metrics (height, weight, activity level, dietary preference, etc.) for a user.",
)
def update_health_profile_endpoint(
    user_id: uuid.UUID,
    profile_in: HealthProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HealthProfileResponse:
    ensure_user_ownership(current_user, user_id)
    profile = health_profile_service.update_profile(db, user_id, profile_in)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Health profile not found for user '{user_id}'.",
        )
    return profile


@router.delete(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Health Profile",
    description="Delete health profile for a specific user.",
)
def delete_health_profile_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    ensure_user_ownership(current_user, user_id)
    success = health_profile_service.delete_profile(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Health profile not found for user '{user_id}'.",
        )
    return {"message": "Health profile deleted successfully", "user_id": str(user_id)}

