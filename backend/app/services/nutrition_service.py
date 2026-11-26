import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food import Food
from app.models.health_profile import HealthProfile
from app.models.meal_recommendation import MealRecommendation
from app.models.meal_recommendation_item import MealRecommendationItem
from app.models.user import User
from app.schemas.nutrition import (
    MealRecommendationRequest,
    MealRecommendationResponse,
    RecommendedFoodItem,
)
from app.services.food_service import list_foods, seed_sample_foods_if_empty
from app.services.nutrition_engine import (
    ConstraintEngine,
    MealComposer,
)


def generate_recommendation(
    db: Session, request: MealRecommendationRequest
) -> MealRecommendationResponse:
    # 1. Ensure test foods are available if database has none
    seed_sample_foods_if_empty(db)

    # 2. Get user's health profile if exists
    stmt_profile = select(HealthProfile).where(HealthProfile.user_id == request.user_id)
    health_profile = db.scalars(stmt_profile).first()

    # 3. Retrieve all candidate food items
    all_foods = list_foods(db, limit=200)

    # 4. Apply Constraint Engine
    candidates = ConstraintEngine.filter_foods(
        foods=all_foods,
        request=request,
        health_profile=health_profile,
    )

    # 5. Compose balanced meal using Scoring Engine and Plate Method
    active_preference = (
        request.dietary_preference
        or (health_profile.dietary_preference if health_profile else None)
    )
    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=candidates,
        meal_type=request.meal_type,
        preference=active_preference,
        custom_target=request.custom_target,
    )

    # 6. Calculate total nutrients
    tot_energy = round(sum(i.energy_kcal * i.serving_multiplier for i in items), 1)
    tot_carb = round(sum(i.carbohydrate_g * i.serving_multiplier for i in items), 1)
    tot_protein = round(sum(i.protein_g * i.serving_multiplier for i in items), 1)
    tot_fat = round(sum(i.fat_g * i.serving_multiplier for i in items), 1)
    tot_fiber = round(sum((i.fiber_g or 0) * i.serving_multiplier for i in items), 1)

    rec_id = uuid.uuid4()
    algorithm_version = "v1.0-rule_scoring"
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # 7. Construct response
    response_data = MealRecommendationResponse(
        recommendation_id=rec_id,
        user_id=request.user_id,
        meal_type=request.meal_type,
        algorithm_version=algorithm_version,
        generated_at=now,
        items=items,
        total_energy_kcal=tot_energy,
        total_carbohydrate_g=tot_carb,
        total_protein_g=tot_protein,
        total_fat_g=tot_fat,
        total_fiber_g=tot_fiber,
        meal_balance_evaluation=meal_eval,
        safety_notes=safety_notes,
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )

    # 8. Save recommendation history snapshot in PostgreSQL
    input_snapshot = request.model_dump(mode="json")
    result_snapshot = response_data.model_dump(mode="json")

    recommendation_record = MealRecommendation(
        id=rec_id,
        user_id=request.user_id,
        meal_type=request.meal_type,
        algorithm_version=algorithm_version,
        input_snapshot=input_snapshot,
        recommendation_result=result_snapshot,
    )
    db.add(recommendation_record)
    db.flush()

    # 9. Save relational recommendation items
    for item in items:
        rec_item = MealRecommendationItem(
            id=uuid.uuid4(),
            recommendation_id=rec_id,
            food_id=item.food_id,
            serving_multiplier=Decimal(str(item.serving_multiplier)),
            calculated_energy_kcal=Decimal(str(item.energy_kcal)),
            calculated_carbohydrate_g=Decimal(str(item.carbohydrate_g)),
            calculated_protein_g=Decimal(str(item.protein_g)),
            calculated_fat_g=Decimal(str(item.fat_g)),
            calculated_fiber_g=Decimal(str(item.fiber_g or 0)),
            score=Decimal(str(item.score)),
            reason="; ".join(item.reasons[:2]),
        )
        db.add(rec_item)

    db.commit()
    return response_data


def get_recommendation_history(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> List[MealRecommendation]:
    """Retrieve historical recommendation snapshots for a user."""
    stmt = (
        select(MealRecommendation)
        .where(MealRecommendation.user_id == user_id)
        .order_by(MealRecommendation.generated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
