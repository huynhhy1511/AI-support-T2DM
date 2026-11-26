import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_user_ownership, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.glucose_record import (
    GlucoseRecordCreate,
    GlucoseRecordResponse,
    GlucoseRecordUpdate,
    GlucoseStatsResponse,
)
from app.services import glucose_service, user_service

router = APIRouter(prefix="/glucose-records", tags=["glucose-records"])


@router.post(
    "",
    response_model=GlucoseRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Glucose Measurement",
    description="Record a new blood glucose reading for a user with context (fasting, after_meal, etc.) and note.",
)
def create_glucose_record_endpoint(
    record_in: GlucoseRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlucoseRecordResponse:
    ensure_user_ownership(current_user, record_in.user_id)
    # 1. Verify user exists
    user = user_service.get_user_by_id(db, record_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{record_in.user_id}' does not exist.",
        )

    return glucose_service.create_glucose_record(db, record_in)


@router.get(
    "/user/{user_id}",
    response_model=List[GlucoseRecordResponse],
    summary="List Glucose Records for User",
    description="Retrieve historical glucose measurements for a specific user, sorted from newest to oldest.",
)
def list_user_glucose_records_endpoint(
    user_id: uuid.UUID,
    start_time: Optional[datetime] = Query(None, description="Filter records measured on or after this timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter records measured on or before this timestamp"),
    context: Optional[str] = Query(None, description="Filter by context: fasting, before_meal, after_meal, random, other"),
    unit: Optional[str] = Query(None, description="Filter by unit: mmol/L or mg/dL"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GlucoseRecordResponse]:
    ensure_user_ownership(current_user, user_id)
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' does not exist.",
        )

    return glucose_service.list_glucose_records(
        db,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        context=context,
        unit=unit,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/user/{user_id}/stats",
    response_model=GlucoseStatsResponse,
    summary="Get Glucose Statistics for User",
    description="Calculate average, minimum, maximum, and total count of blood glucose measurements.",
)
def get_user_glucose_stats_endpoint(
    user_id: uuid.UUID,
    unit: str = Query("mmol/L", description="Target unit for statistics ('mmol/L' or 'mg/dL')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlucoseStatsResponse:
    ensure_user_ownership(current_user, user_id)
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' does not exist.",
        )

    return glucose_service.get_glucose_statistics(db, user_id=user_id, unit=unit)


@router.get(
    "/{record_id}",
    response_model=GlucoseRecordResponse,
    summary="Get Glucose Record by ID",
    description="Retrieve details of a single blood glucose record.",
)
def get_glucose_record_endpoint(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlucoseRecordResponse:
    record = glucose_service.get_glucose_record_by_id(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glucose record with id '{record_id}' not found.",
        )
    ensure_user_ownership(current_user, record.user_id)
    return record


@router.put(
    "/{record_id}",
    response_model=GlucoseRecordResponse,
    summary="Update Glucose Record",
    description="Update a blood glucose reading value, unit, context, or note.",
)
def update_glucose_record_endpoint(
    record_id: uuid.UUID,
    record_in: GlucoseRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlucoseRecordResponse:
    existing = glucose_service.get_glucose_record_by_id(db, record_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glucose record with id '{record_id}' not found.",
        )
    ensure_user_ownership(current_user, existing.user_id)
    record = glucose_service.update_glucose_record(db, record_id, record_in)
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Glucose Record",
    description="Delete a single blood glucose measurement record.",
)
def delete_glucose_record_endpoint(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    existing = glucose_service.get_glucose_record_by_id(db, record_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glucose record with id '{record_id}' not found.",
        )
    ensure_user_ownership(current_user, existing.user_id)
    success = glucose_service.delete_glucose_record(db, record_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glucose record with id '{record_id}' not found.",
        )
    return {"message": "Glucose record deleted successfully", "record_id": str(record_id)}

