import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food import Food
from app.models.health_profile import HealthProfile
from app.models.meal_recommendation import MealRecommendation
from app.models.meal_recommendation_item import MealRecommendationItem
from app.schemas.nutrition import (
    DailyMealPlanRequest,
    DailyMealPlanResponse,
    FoodSubstitutionRequest,
    FoodSubstitutionResponse,
    MealRecommendationRequest,
    MealRecommendationResponse,
    MealType,
    RecommendedFoodItem,
)
from app.services.food_service import get_food_by_id, list_foods, seed_sample_foods_if_empty
from app.services.nutrition_engine import (
    ConstraintEngine,
    EnergyCalculator,
    MealComposer,
    NutritionSafetyGuard,
)


def _build_abstained_meal_response(
    user_id: uuid.UUID,
    meal_type: str,
    reason: str,
    missing_fields: Optional[List[str]] = None,
    extra_notes: Optional[List[str]] = None,
) -> MealRecommendationResponse:
    return MealRecommendationResponse(
        recommendation_id=uuid.uuid4(),
        user_id=user_id,
        meal_type=meal_type,
        algorithm_version="v1.1-safety_guarded",
        generated_at=datetime.now(timezone.utc),
        items=[],
        total_energy_kcal=0.0,
        total_carbohydrate_g=0.0,
        total_protein_g=0.0,
        total_fat_g=0.0,
        total_fiber_g=0.0,
        total_sodium_mg=0.0,
        meal_balance_evaluation="Không thể tạo thực đơn tự động do giới hạn an toàn hoặc thiếu thông tin.",
        safety_notes=extra_notes or [reason],
        is_abstained=True,
        abstention_reason=reason,
        missing_profile_fields=missing_fields or [],
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )


def generate_recommendation(
    db: Session,
    request: MealRecommendationRequest,
    avoid_food_ids: Optional[Set[uuid.UUID]] = None,
    persist: bool = True,
) -> MealRecommendationResponse:
    # 1. Ensure foods are available
    seed_sample_foods_if_empty(db)

    # 2. Fetch user's health profile
    stmt_profile = select(HealthProfile).where(HealthProfile.user_id == request.user_id)
    health_profile = db.scalars(stmt_profile).first()

    # 3. Safety Guard: Profile completeness & Clinical restrictions
    missing_fields = NutritionSafetyGuard.check_profile_completeness(health_profile)
    clinical_check = NutritionSafetyGuard.check_clinical_restrictions(request.comorbidities)

    if clinical_check["is_restricted"]:
        return _build_abstained_meal_response(
            user_id=request.user_id,
            meal_type=request.meal_type,
            reason=str(clinical_check["abstention_reason"]),
            missing_fields=missing_fields,
        )

    if request.require_complete_profile and missing_fields:
        reason = (
            f"Hồ sơ sức khỏe chưa đủ thông tin cơ bản để cá thể hóa thực đơn "
            f"(thiếu: {', '.join(missing_fields)}). Vui lòng bổ sung thông tin hồ sơ trước khi tiếp tục."
        )
        return _build_abstained_meal_response(
            user_id=request.user_id,
            meal_type=request.meal_type,
            reason=reason,
            missing_fields=missing_fields,
        )

    # 4. Retrieve candidate foods from PostgreSQL (prefer verified non-test data if available)
    all_foods = list_foods(db, limit=200)
    official_foods = [f for f in all_foods if not f.is_test_data]
    food_pool = official_foods if official_foods else all_foods

    # 5. Apply Constraint Engine (strictly NO fallback to unsafe foods)
    active_preference = (
        request.dietary_preference
        or (health_profile.dietary_preference if health_profile else None)
    )
    pref_low_sodium = (active_preference or "").lower().strip() in ["low_sodium", "it_muoi", "ít muối"]
    low_sodium_required = bool(clinical_check["low_sodium_required"]) or pref_low_sodium

    candidates = ConstraintEngine.filter_foods(
        foods=food_pool,
        request=request,
        health_profile=health_profile,
        low_sodium_required=low_sodium_required,
    )

    if not candidates:
        return _build_abstained_meal_response(
            user_id=request.user_id,
            meal_type=request.meal_type,
            reason=(
                "Không tìm thấy thực phẩm nào trong cơ sở dữ liệu đáp ứng đồng thời tất cả "
                "các ràng buộc về dị ứng, chế độ ăn và bệnh đồng mắc của bạn."
            ),
            missing_fields=missing_fields,
        )

    # 6. Calculate individualized energy target (BMR/TDEE) if profile is complete
    energy_info = EnergyCalculator.calculate_daily_target(
        health_profile=health_profile,
        nutrition_goal=request.nutrition_goal,
    )
    daily_target_kcal = energy_info.get("target_kcal")
    target_meal_kcal = (
        round(float(daily_target_kcal) * EnergyCalculator.MEAL_RATIOS.get(request.meal_type, 0.25), 1)
        if daily_target_kcal
        else None
    )

    # 7. Compose balanced meal using Scoring Engine and Plate Method
    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=candidates,
        meal_type=request.meal_type,
        preference=active_preference,
        custom_target=request.custom_target,
        low_sodium_required=low_sodium_required,
        nutrition_goal=request.nutrition_goal,
        avoid_food_ids=avoid_food_ids,
        target_meal_kcal=target_meal_kcal,
    )

    # Prepend clinical notes, energy notes & incomplete profile limitation notice
    combined_notes: List[str] = list(clinical_check["notes"])
    combined_notes.extend(energy_info.get("notes") or [])
    if pref_low_sodium and not clinical_check["low_sodium_required"]:
        combined_notes.append("Chế độ ăn ít muối (low_sodium): ưu tiên thực phẩm có hàm lượng natri thấp.")
    if missing_fields:
        combined_notes.append(
            f"Lưu ý giới hạn cá thể hóa: Hồ sơ chưa có đầy đủ ({', '.join(missing_fields)}); "
            "thực đơn được tạo ở mức tham khảo chung theo Plate Method."
        )
    combined_notes.extend(safety_notes)

    # 7. Calculate total nutrients consistently using serving_multiplier
    tot_energy = round(sum(i.energy_kcal * i.serving_multiplier for i in items), 1)
    tot_carb = round(sum(i.carbohydrate_g * i.serving_multiplier for i in items), 1)
    tot_protein = round(sum(i.protein_g * i.serving_multiplier for i in items), 1)
    tot_fat = round(sum(i.fat_g * i.serving_multiplier for i in items), 1)
    tot_fiber = round(sum((i.fiber_g or 0.0) * i.serving_multiplier for i in items), 1)
    tot_sodium = round(sum((i.sodium_mg or 0.0) * i.serving_multiplier for i in items), 1)

    rec_id = uuid.uuid4()
    algorithm_version = "v1.1-safety_guarded"
    now = datetime.now(timezone.utc)

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
        total_sodium_mg=tot_sodium,
        meal_balance_evaluation=meal_eval,
        safety_notes=combined_notes,
        is_abstained=False,
        abstention_reason=None,
        missing_profile_fields=missing_fields,
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )

    if persist and items:
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

        for item in items:
            rec_item = MealRecommendationItem(
                id=uuid.uuid4(),
                recommendation_id=rec_id,
                food_id=item.food_id,
                serving_multiplier=Decimal(str(item.serving_multiplier)),
                calculated_energy_kcal=Decimal(str(round(item.energy_kcal * item.serving_multiplier, 2))),
                calculated_carbohydrate_g=Decimal(str(round(item.carbohydrate_g * item.serving_multiplier, 2))),
                calculated_protein_g=Decimal(str(round(item.protein_g * item.serving_multiplier, 2))),
                calculated_fat_g=Decimal(str(round(item.fat_g * item.serving_multiplier, 2))),
                calculated_fiber_g=Decimal(str(round((item.fiber_g or 0.0) * item.serving_multiplier, 2))),
                score=Decimal(str(item.score)),
                reason="; ".join(item.reasons[:2]),
            )
            db.add(rec_item)

        db.commit()

    return response_data


def generate_daily_plan(
    db: Session, request: DailyMealPlanRequest
) -> DailyMealPlanResponse:
    """Tạo thực đơn đầy đủ cả ngày (sáng, trưa, tối, phụ) với đa dạng món ăn và tổng dinh dưỡng."""
    meal_types: List[MealType] = ["breakfast", "lunch", "dinner", "snack"]
    meals: Dict[str, MealRecommendationResponse] = {}
    used_food_ids: Set[uuid.UUID] = set()

    for mtype in meal_types:
        sub_req = MealRecommendationRequest(
            user_id=request.user_id,
            meal_type=mtype,
            dietary_preference=request.dietary_preference,
            excluded_food_ids=request.excluded_food_ids,
            excluded_keywords=request.excluded_keywords,
            allergies=request.allergies,
            comorbidities=request.comorbidities,
            nutrition_goal=request.nutrition_goal,
            require_complete_profile=request.require_complete_profile,
        )
        res = generate_recommendation(
            db=db,
            request=sub_req,
            avoid_food_ids=used_food_ids,
            persist=False,
        )
        if res.is_abstained:
            return DailyMealPlanResponse(
                plan_id=uuid.uuid4(),
                user_id=request.user_id,
                algorithm_version="v1.1-safety_guarded",
                generated_at=datetime.now(timezone.utc),
                meals={},
                daily_total_energy_kcal=0.0,
                daily_total_carbohydrate_g=0.0,
                daily_total_protein_g=0.0,
                daily_total_fat_g=0.0,
                daily_total_fiber_g=0.0,
                daily_total_sodium_mg=0.0,
                macro_distribution_pct={"carb_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0},
                safety_notes=res.safety_notes,
                is_abstained=True,
                abstention_reason=res.abstention_reason,
                missing_profile_fields=res.missing_profile_fields,
                clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
            )

        meals[mtype] = res
        for item in res.items:
            used_food_ids.add(item.food_id)

    tot_kcal = round(sum(m.total_energy_kcal for m in meals.values()), 1)
    tot_carb = round(sum(m.total_carbohydrate_g for m in meals.values()), 1)
    tot_protein = round(sum(m.total_protein_g for m in meals.values()), 1)
    tot_fat = round(sum(m.total_fat_g for m in meals.values()), 1)
    tot_fiber = round(sum(m.total_fiber_g for m in meals.values()), 1)
    tot_sodium = round(sum(m.total_sodium_mg for m in meals.values()), 1)

    macro_kcal = (tot_carb * 4.0) + (tot_protein * 4.0) + (tot_fat * 9.0)
    if macro_kcal > 0:
        macro_pct = {
            "carb_pct": round((tot_carb * 4.0 / macro_kcal) * 100, 1),
            "protein_pct": round((tot_protein * 4.0 / macro_kcal) * 100, 1),
            "fat_pct": round((tot_fat * 9.0 / macro_kcal) * 100, 1),
        }
    else:
        macro_pct = {"carb_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}

    daily_notes: List[str] = []
    if tot_fiber < 20.0:
        daily_notes.append(
            f"Tổng chất xơ cả ngày ({tot_fiber:.1f}g) còn thấp hơn khuyến nghị (>= 20-25g/ngày); nên bổ sung thêm rau xanh."
        )
    if tot_sodium > 2000.0:
        daily_notes.append(
            f"Tổng lượng natri ước tính ({tot_sodium:.0f}mg) vượt 2000mg/ngày; lưu ý nêm nhạt khi chế biến."
        )

    first_meal = next(iter(meals.values()))
    return DailyMealPlanResponse(
        plan_id=uuid.uuid4(),
        user_id=request.user_id,
        algorithm_version="v1.1-safety_guarded",
        generated_at=datetime.now(timezone.utc),
        meals=meals,
        daily_total_energy_kcal=tot_kcal,
        daily_total_carbohydrate_g=tot_carb,
        daily_total_protein_g=tot_protein,
        daily_total_fat_g=tot_fat,
        daily_total_fiber_g=tot_fiber,
        daily_total_sodium_mg=tot_sodium,
        macro_distribution_pct=macro_pct,
        safety_notes=daily_notes,
        is_abstained=False,
        abstention_reason=None,
        missing_profile_fields=first_meal.missing_profile_fields,
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )


def substitute_food(
    db: Session, request: FoodSubstitutionRequest
) -> Optional[FoodSubstitutionResponse]:
    """Đề xuất các món ăn thay thế phù hợp cùng nhóm và thỏa mãn ràng buộc người dùng."""
    original_food = get_food_by_id(db, request.food_id_to_replace)
    if not original_food:
        return None

    stmt_profile = select(HealthProfile).where(HealthProfile.user_id == request.user_id)
    health_profile = db.scalars(stmt_profile).first()

    clinical_check = NutritionSafetyGuard.check_clinical_restrictions(request.comorbidities)
    if clinical_check["is_restricted"]:
        return FoodSubstitutionResponse(
            original_food_id=original_food.id,
            original_food_name=original_food.name,
            category=original_food.category,
            substitutes=[],
            message=str(clinical_check["abstention_reason"]),
        )

    all_foods = list_foods(db, limit=200)
    official_foods = [f for f in all_foods if not f.is_test_data]
    food_pool = official_foods if official_foods else all_foods

    dummy_req = MealRecommendationRequest(
        user_id=request.user_id,
        meal_type=request.meal_type,
        dietary_preference=request.dietary_preference,
        excluded_food_ids=request.excluded_food_ids,
        excluded_keywords=request.excluded_keywords,
        allergies=request.allergies,
        comorbidities=request.comorbidities,
    )
    candidates = ConstraintEngine.filter_foods(
        foods=food_pool,
        request=dummy_req,
        health_profile=health_profile,
        low_sodium_required=bool(clinical_check["low_sodium_required"]),
    )

    active_pref = (
        request.dietary_preference
        or (health_profile.dietary_preference if health_profile else None)
    )
    substitutes = MealComposer.suggest_substitutes(
        candidate_foods=candidates,
        food_to_replace=original_food,
        preference=active_pref,
        low_sodium_required=bool(clinical_check["low_sodium_required"]),
        limit=request.limit,
    )

    msg = (
        f"Tìm thấy {len(substitutes)} món thay thế phù hợp trong nhóm '{original_food.category}'."
        if substitutes
        else f"Không tìm thấy món thay thế phù hợp trong nhóm '{original_food.category}' thỏa mãn ràng buộc."
    )
    return FoodSubstitutionResponse(
        original_food_id=original_food.id,
        original_food_name=original_food.name,
        category=original_food.category,
        substitutes=substitutes,
        message=msg,
    )


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
