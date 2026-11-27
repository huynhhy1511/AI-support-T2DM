import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal_diary import (
    MealLogCreate,
    MealLogListResponse,
    MealLogResponse,
    MealLogUpdate,
    NutritionProgressResponse,
    WeightRecordCreate,
    WeightRecordResponse,
)
from app.schemas.nutrition import MealType
from app.services import meal_diary_service

router = APIRouter(prefix="/nutrition", tags=["nutrition-diary-progress"])


@router.post(
    "/meal-logs",
    response_model=MealLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Meal Log",
    description="Record an actual meal diary entry with backend-computed item nutrition without mutating recommendations.",
)
def create_meal_log_endpoint(
    payload: MealLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealLogResponse:
    return meal_diary_service.create_meal_log(db, current_user.id, payload)


@router.get(
    "/meal-logs",
    response_model=MealLogListResponse,
    summary="List Meal Logs",
    description="Retrieve authenticated user's meal logs with optional date range, meal_type filters, and pagination.",
)
def list_meal_logs_endpoint(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    meal_type: Optional[MealType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealLogListResponse:
    return meal_diary_service.list_meal_logs(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        meal_type=meal_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/meal-logs/{log_id}",
    response_model=MealLogResponse,
    summary="Get Meal Log Detail",
    description="Retrieve details of a single meal log (owner only).",
)
def get_meal_log_endpoint(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealLogResponse:
    return meal_diary_service.get_meal_log(db, log_id, current_user.id)


@router.patch(
    "/meal-logs/{log_id}",
    response_model=MealLogResponse,
    summary="Update Meal Log",
    description="Update status, notes, or items of a meal log and recalculate actual nutrition.",
)
def update_meal_log_endpoint(
    log_id: uuid.UUID,
    payload: MealLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealLogResponse:
    return meal_diary_service.update_meal_log(db, log_id, current_user.id, payload)


@router.delete(
    "/meal-logs/{log_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Meal Log",
    description="Delete a meal log entry (owner only).",
)
def delete_meal_log_endpoint(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    meal_diary_service.delete_meal_log(db, log_id, current_user.id)
    return {"message": "Meal log deleted successfully", "log_id": str(log_id)}


@router.post(
    "/progress/weight",
    response_model=WeightRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Record or Update Daily Weight",
    description="Upsert weight measurement for recorded_at and synchronize latest weight to HealthProfile.",
)
def upsert_weight_endpoint(
    payload: WeightRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeightRecordResponse:
    return meal_diary_service.upsert_weight_record(db, current_user.id, payload)


@router.get(
    "/progress/weight",
    response_model=List[WeightRecordResponse],
    summary="List Weight History",
    description="Retrieve user's weight records ordered chronologically ascending.",
)
def list_weight_endpoint(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[WeightRecordResponse]:
    return meal_diary_service.list_weight_records(
        db, current_user.id, date_from=date_from, date_to=date_to
    )


@router.get(
    "/progress",
    response_model=NutritionProgressResponse,
    summary="Get Nutrition & Weight Progress",
    description="Aggregate meal logging adherence, planned vs actual daily trends, and weight history.",
)
def get_nutrition_progress_endpoint(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NutritionProgressResponse:
    return meal_diary_service.get_nutrition_progress(
        db, current_user.id, date_from=date_from, date_to=date_to
    )
