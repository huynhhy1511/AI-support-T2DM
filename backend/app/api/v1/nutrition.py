import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_user_ownership, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.nutrition import (
    MealRecommendationRequest,
    MealRecommendationResponse,
)
from app.services import nutrition_service, user_service

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post(
    "/recommend",
    response_model=MealRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Meal Recommendation",
    description=(
        "Generate a tailored meal recommendation for a Type 2 Diabetes patient based on "
        "their health profile, meal type, dietary preferences, and carbohydrate targets. "
        "Applies rule-based constraints, nutrient scoring, and Plate Method balancing."
    ),
)
def recommend_meal_endpoint(
    request: MealRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealRecommendationResponse:
    ensure_user_ownership(current_user, request.user_id)
    # 1. Verify user exists
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{request.user_id}' does not exist.",
        )

    return nutrition_service.generate_recommendation(db, request)


@router.get(
    "/recommendations/user/{user_id}",
    response_model=List[Dict[str, Any]],
    summary="Get User Meal Recommendation History",
    description="Retrieve past meal recommendation snapshots generated for a user.",
)
def get_user_recommendations_endpoint(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    ensure_user_ownership(current_user, user_id)
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' does not exist.",
        )

    records = nutrition_service.get_recommendation_history(
        db, user_id=user_id, skip=skip, limit=limit
    )
    return [
        {
            "id": r.id,
            "meal_type": r.meal_type,
            "algorithm_version": r.algorithm_version,
            "generated_at": r.generated_at,
            "result": r.recommendation_result,
        }
        for r in records
    ]

