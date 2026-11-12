import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Register a new user account with email, optional display name, and consent status.",
)
def create_user_endpoint(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = user_service.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{user_in.email}' already exists.",
        )
    return user_service.create_user(db, user_in)


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List Users",
    description="Retrieve a paginated list of registered users.",
)
def list_users_endpoint(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Max number of users to return"),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    return user_service.list_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
    description="Retrieve details of a user by their UUID.",
)
def get_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update display name or consent status of an existing user.",
)
def update_user_endpoint(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = user_service.update_user(db, user_id, user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete User",
    description="Delete a user and cascade-delete health profile and glucose records.",
)
def delete_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return {"message": "User deleted successfully", "user_id": str(user_id)}

