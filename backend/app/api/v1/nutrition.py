import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.nutrition import (
    DailyMealPlanRequest,
    DailyMealPlanResponse,
    FoodSubstitutionRequest,
    FoodSubstitutionResponse,
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
        "their health profile, meal type, dietary preferences, allergies, comorbidities, and carbohydrate targets."
    ),
)
def recommend_meal_endpoint(
    request: MealRecommendationRequest,
    db: Session = Depends(get_db),
) -> MealRecommendationResponse:
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{request.user_id}' does not exist.",
        )

    return nutrition_service.generate_recommendation(db, request)


@router.post(
    "/recommend-daily",
    response_model=DailyMealPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Full-Day Meal Plan",
    description=(
        "Generate a full-day meal plan (breakfast, lunch, dinner, snack) with daily macro totals "
        "and safety checks for allergies, comorbidities, and profile completeness."
    ),
)
def recommend_daily_plan_endpoint(
    request: DailyMealPlanRequest,
    db: Session = Depends(get_db),
) -> DailyMealPlanResponse:
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{request.user_id}' does not exist.",
        )

    return nutrition_service.generate_daily_plan(db, request)


@router.post(
    "/substitute",
    response_model=FoodSubstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest Food Substitutes",
    description="Suggest alternative foods in the same category satisfying user allergies and dietary constraints.",
)
def substitute_food_endpoint(
    request: FoodSubstitutionRequest,
    db: Session = Depends(get_db),
) -> FoodSubstitutionResponse:
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{request.user_id}' does not exist.",
        )

    res = nutrition_service.substitute_food(db, request)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food with id '{request.food_id_to_replace}' does not exist.",
        )
    return res


@router.post(
    "/explain",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Generate Daily Meal Plan with RAG Explanation",
    description="Generate a full-day meal plan via the Recommendation Engine and explain it using RAG + LLM with verified medical citations.",
)
def recommend_and_explain_endpoint(
    request: DailyMealPlanRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    import sys
    from pathlib import Path

    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{request.user_id}' does not exist.",
        )

    plan = nutrition_service.generate_daily_plan(db, request)
    plan_dict = plan.model_dump(mode="json")

    root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    from nutrition_rag import NutritionRAGExplainer

    explainer = NutritionRAGExplainer()
    rag_result = explainer.explain_meal_plan(
        meal_plan=plan_dict,
        user_profile=request.model_dump(mode="json"),
    )
    return {
        "meal_plan": plan_dict,
        "rag_explanation": rag_result,
    }


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
) -> List[Dict[str, Any]]:
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
