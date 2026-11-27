import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health_profile import HealthProfile
from app.models.meal_recommendation import MealRecommendation
from app.models.meal_recommendation_item import MealRecommendationItem
from app.schemas.nutrition import (
    DailyNutritionSummary,
    DailyRecommendationsResponse,
    FoodSubstitutionRequest,
    MealRecommendationRequest,
    MealRecommendationResponse,
    NutritionTarget,
    RecommendedFoodItem,
    SafetyAlertSchema,
    SafetyAlertsResponse,
)
from app.services.food_service import get_food_by_id, list_foods
from app.services.health_profile_service import (
    compute_profile_completeness,
    get_profile_by_user_id,
)
from app.services.nutrition_engine import (
    ConstraintEngine,
    MealComposer,
    NutritionScoringEngine,
)


def _has_ckd(comorbidities: Optional[List[str]]) -> bool:
    if not comorbidities:
        return False
    return any(
        isinstance(c, str)
        and any(tok in c.lower() for tok in ("ckd", "chronic_kidney", "bệnh thận"))
        for c in comorbidities
    )


def _has_hypertension(comorbidities: Optional[List[str]]) -> bool:
    if not comorbidities:
        return False
    return any(
        isinstance(c, str)
        and any(tok in c.lower() for tok in ("hypertension", "tăng huyết áp"))
        for c in comorbidities
    )


def _merge_allergens(
    profile_allergies: Optional[List[str]],
    request_allergens: Optional[List[str]],
) -> Optional[List[str]]:
    merged: List[str] = []
    seen = set()
    for raw in list(profile_allergies or []) + list(request_allergens or []):
        if not isinstance(raw, str):
            continue
        cleaned = raw.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            merged.append(cleaned)
    return merged or None


def generate_recommendation(
    db: Session, request: MealRecommendationRequest
) -> MealRecommendationResponse:
    # 1. Get user's health profile if exists
    stmt_profile = select(HealthProfile).where(HealthProfile.user_id == request.user_id)
    health_profile = db.scalars(stmt_profile).first()

    rec_id = uuid.uuid4()
    algorithm_version = "v1.0-rule_scoring"
    now = datetime.now(timezone.utc)

    # 1b. Clinical Safety Guard: intentionally abstain when CKD comorbidity is present
    profile_comorbidities = (
        getattr(health_profile, "comorbidities", None) if health_profile else None
    )
    if health_profile is not None and _has_ckd(profile_comorbidities):
        return MealRecommendationResponse(
            recommendation_id=rec_id,
            user_id=request.user_id,
            meal_type=request.meal_type,
            status="abstained",
            reason_code="CKD_SPECIALIST_REQUIRED",
            algorithm_version=algorithm_version,
            generated_at=now,
            items=[],
            total_energy_kcal=0.0,
            total_carbohydrate_g=0.0,
            total_protein_g=0.0,
            total_fat_g=0.0,
            total_fiber_g=0.0,
            meal_balance_evaluation=(
                "Hệ thống tạm dừng đề xuất thực đơn tự động do hồ sơ ghi nhận bệnh thận mạn (CKD). "
                "Chế độ ăn cho người bệnh đái tháo đường kèm CKD cần kiểm soát chặt chẽ đạm, kali, photpho và natri "
                "theo phác đồ cá nhân hóa của bác sĩ chuyên khoa thận hoặc chuyên gia dinh dưỡng lâm sàng."
            ),
            safety_notes=[
                "Cảnh báo chuyên môn (CKD_SPECIALIST_REQUIRED): Không tự động sinh thực đơn đối với bệnh nhân có bệnh thận mạn (CKD). "
                "Vui lòng liên hệ bác sĩ điều trị hoặc chuyên gia dinh dưỡng để được thiết kế khẩu phần an toàn."
            ],
            clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
        )

    # 2. Retrieve all candidate food items
    all_foods = list_foods(db, limit=200)

    # 3. Merge profile allergies with request allergies and apply Constraint Engine
    profile_allergies = (
        getattr(health_profile, "allergies", None) if health_profile else None
    )
    merged_allergens = _merge_allergens(profile_allergies, request.excluded_allergens)
    effective_request = request.model_copy(
        update={"excluded_allergens": merged_allergens}
    )

    candidates = ConstraintEngine.filter_foods(
        foods=all_foods,
        request=effective_request,
        health_profile=health_profile,
    )

    # 4. Compose balanced meal using Scoring Engine and Plate Method
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

    # 5. Calculate total nutrients (items already contain scaled nutrients)
    tot_energy = round(sum(i.energy_kcal for i in items), 2)
    tot_carb = round(sum(i.carbohydrate_g for i in items), 2)
    tot_protein = round(sum(i.protein_g for i in items), 2)
    tot_fat = round(sum(i.fat_g for i in items), 2)
    tot_fiber = round(sum((i.fiber_g or 0) for i in items), 2)
    tot_sodium = round(sum(i.sodium_mg for i in items if i.sodium_mg is not None), 2)
    tot_sat_fat = round(
        sum(i.saturated_fat_g for i in items if i.saturated_fat_g is not None), 2
    )

    # 6. Construct response
    response_data = MealRecommendationResponse(
        recommendation_id=rec_id,
        user_id=request.user_id,
        meal_type=request.meal_type,
        status="generated",
        reason_code=None,
        algorithm_version=algorithm_version,
        generated_at=now,
        items=items,
        total_energy_kcal=tot_energy,
        total_carbohydrate_g=tot_carb,
        total_protein_g=tot_protein,
        total_fat_g=tot_fat,
        total_fiber_g=tot_fiber,
        total_sodium_mg=tot_sodium,
        total_saturated_fat_g=tot_sat_fat,
        meal_balance_evaluation=meal_eval,
        safety_notes=safety_notes,
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )

    # 7. Save recommendation history snapshot in PostgreSQL
    input_snapshot = effective_request.model_dump(mode="json")
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

    # 8. Save relational recommendation items
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
            reason="; ".join(item.reasons),
        )
        db.add(rec_item)

    db.commit()
    return response_data


def evaluate_safety_alerts(db: Session, user_id: uuid.UUID) -> SafetyAlertsResponse:
    """Evaluate active clinical safety alerts from the user's health profile."""
    profile = get_profile_by_user_id(db, user_id)
    completeness = compute_profile_completeness(profile)
    alerts: List[SafetyAlertSchema] = []
    has_blocking_condition = False

    if not completeness.is_complete:
        alerts.append(
            SafetyAlertSchema(
                code="MISSING_PROFILE_FIELDS",
                level="warning",
                title="Hồ sơ dinh dưỡng chưa đầy đủ thông tin",
                message=(
                    "Thiếu các chỉ số nhân trắc học hoặc mức vận động bắt buộc để tính "
                    "BMR/TDEE theo công thức Mifflin-St Jeor."
                ),
                action_guidance="Vui lòng bổ sung đầy đủ các trường còn thiếu trong Hồ sơ dinh dưỡng.",
                details=completeness.missing_fields,
            )
        )

    comorbidities = list(profile.comorbidities or []) if profile else []
    if _has_ckd(comorbidities):
        has_blocking_condition = True
        alerts.append(
            SafetyAlertSchema(
                code="CKD_SPECIALIST_REQUIRED",
                level="critical",
                title="Bệnh thận mạn (CKD) — Giới hạn phạm vi tự động",
                message=(
                    "Hồ sơ có ghi nhận bệnh thận mạn (CKD). Hệ thống tạm dừng đề xuất thực đơn tự động "
                    "vì cần kiểm soát nghiêm ngặt lượng đạm, kali, photpho và natri."
                ),
                action_guidance="Vui lòng tham khảo trực tiếp bác sĩ chuyên khoa thận hoặc chuyên gia dinh dưỡng lâm sàng.",
                details=["comorbidity:ckd"],
            )
        )

    if _has_hypertension(comorbidities):
        alerts.append(
            SafetyAlertSchema(
                code="HYPERTENSION_SODIUM_LIMIT",
                level="warning",
                title="Tăng huyết áp — Kiểm soát nghiêm ngặt Natri",
                message=(
                    "Người bệnh đái tháo đường kèm tăng huyết áp cần giới hạn lượng natri (< 2.000 mg/ngày) "
                    "và ưu tiên các món ít muối."
                ),
                action_guidance="Hạn chế nước chấm, thực phẩm chế biến sẵn và chọn chế độ ít muối (low_sodium).",
                details=["comorbidity:hypertension"],
            )
        )

    bmi_category: Optional[str] = None
    bmi = completeness.bmi
    if bmi is not None:
        if bmi < 18.5:
            bmi_category = "underweight"
            alerts.append(
                SafetyAlertSchema(
                    code="BMI_UNDERWEIGHT",
                    level="warning",
                    title="Chỉ số BMI ở mức thiếu cân (< 18.5)",
                    message=f"BMI hiện tại là {bmi:.2f} kg/m². Không khuyến nghị áp dụng chế độ thâm hụt năng lượng giảm cân.",
                    action_guidance="Nên chọn mục tiêu duy trì/cải thiện dinh dưỡng và tham khảo bác sĩ điều trị.",
                    details=[f"bmi:{bmi:.2f}"],
                )
            )
        elif bmi < 25.0:
            bmi_category = "normal"
        elif bmi < 30.0:
            bmi_category = "overweight"
            alerts.append(
                SafetyAlertSchema(
                    code="BMI_OVERWEIGHT",
                    level="info",
                    title="Chỉ số BMI ở mức thừa cân (25.0 – 29.9)",
                    message=f"BMI hiện tại là {bmi:.2f} kg/m². Có thể cân nhắc kiểm soát năng lượng hợp lý và tăng vận động.",
                    action_guidance="Theo dõi khẩu phần carbohydrate và duy trì vận động vừa phải hằng ngày.",
                    details=[f"bmi:{bmi:.2f}"],
                )
            )
        else:
            bmi_category = "obese"
            alerts.append(
                SafetyAlertSchema(
                    code="BMI_OBESE",
                    level="warning",
                    title="Chỉ số BMI ở mức béo phì (>= 30.0)",
                    message=f"BMI hiện tại là {bmi:.2f} kg/m². Cần lộ trình kiểm soát cân nặng và đường huyết an toàn.",
                    action_guidance="Cân nhắc mục tiêu giảm cân an toàn và trao đổi kế hoạch dài hạn với bác sĩ.",
                    details=[f"bmi:{bmi:.2f}"],
                )
            )

    return SafetyAlertsResponse(
        user_id=user_id,
        has_blocking_condition=has_blocking_condition,
        is_profile_complete=completeness.is_complete,
        bmi=bmi,
        bmi_category=bmi_category,
        target_energy_kcal=completeness.target_energy_kcal,
        alerts=alerts,
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


def substitute_food_in_recommendation(
    db: Session,
    recommendation_id: uuid.UUID,
    current_user_id: uuid.UUID,
    payload: FoodSubstitutionRequest,
) -> MealRecommendationResponse:
    """Replace an item in an existing recommendation after strict ownership, allergy, and safety checks."""
    rec = db.get(MealRecommendation, recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal recommendation '{recommendation_id}' not found.",
        )

    if rec.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this meal recommendation.",
        )

    current_response = MealRecommendationResponse.model_validate(rec.recommendation_result)
    target_idx = next(
        (
            idx
            for idx, item in enumerate(current_response.items)
            if item.food_id == payload.original_food_id
        ),
        None,
    )
    if target_idx is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Original food '{payload.original_food_id}' is not present in this recommendation.",
        )

    replacement_food = get_food_by_id(db, payload.replacement_food_id)
    if not replacement_food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replacement food '{payload.replacement_food_id}' not found.",
        )

    # Validate replacement against user's health profile allergies, request exclusions, and dietary preference
    health_profile = get_profile_by_user_id(db, current_user_id)
    input_snap = rec.input_snapshot or {}
    merged_allergens = _merge_allergens(
        getattr(health_profile, "allergies", None) if health_profile else None,
        input_snap.get("excluded_allergens"),
    )
    active_preference = input_snap.get("dietary_preference") or (
        health_profile.dietary_preference if health_profile else None
    )
    validation_req = MealRecommendationRequest(
        user_id=current_user_id,
        meal_type=rec.meal_type,
        dietary_preference=active_preference,
        excluded_keywords=input_snap.get("excluded_keywords"),
        excluded_allergens=merged_allergens,
    )

    safe_replacement = ConstraintEngine.filter_foods(
        foods=[replacement_food],
        request=validation_req,
        health_profile=health_profile,
    )
    if not safe_replacement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Món thay thế vi phạm ràng buộc dị ứng hoặc chế độ ăn an toàn của bạn. "
                "Thực đơn gốc được giữ nguyên không thay đổi."
            ),
        )

    # Calculate serving multiplier (explicit serving_g or calorie-equivalent auto multiplier)
    original_item = current_response.items[target_idx]
    if payload.serving_g is not None:
        multiplier = round(payload.serving_g / float(replacement_food.serving_size_g), 2)
        multiplier = max(0.1, multiplier)
    else:
        orig_kcal = float(original_item.energy_kcal)
        rep_base_kcal = float(replacement_food.energy_kcal)
        if rep_base_kcal > 0 and orig_kcal > 0:
            raw_mult = orig_kcal / rep_base_kcal
            multiplier = round(max(0.5, min(2.0, raw_mult)), 2)
        else:
            multiplier = 1.0

    score, reasons, warning = NutritionScoringEngine.score_item(
        replacement_food, preference=active_preference
    )
    new_item = MealComposer._to_recommended_item(
        (replacement_food, score, reasons, warning), multiplier=multiplier
    )
    new_item.reasons.append("Đã thay thế món tương đương và kiểm tra lại ràng buộc an toàn")

    updated_items: List[RecommendedFoodItem] = list(current_response.items)
    updated_items[target_idx] = new_item

    # Recalculate totals and re-evaluate safety notes
    raw_custom_target = input_snap.get("custom_target")
    custom_target = (
        NutritionTarget.model_validate(raw_custom_target)
        if isinstance(raw_custom_target, dict)
        else None
    )
    meal_eval, safety_notes = MealComposer.evaluate_meal_safety(
        selected_foods=updated_items,
        meal_type=rec.meal_type,
        custom_target=custom_target,
    )

    tot_energy = round(sum(i.energy_kcal for i in updated_items), 2)
    tot_carb = round(sum(i.carbohydrate_g for i in updated_items), 2)
    tot_protein = round(sum(i.protein_g for i in updated_items), 2)
    tot_fat = round(sum(i.fat_g for i in updated_items), 2)
    tot_fiber = round(sum((i.fiber_g or 0) for i in updated_items), 2)
    tot_sodium = round(
        sum(i.sodium_mg for i in updated_items if i.sodium_mg is not None), 2
    )
    tot_sat_fat = round(
        sum(i.saturated_fat_g for i in updated_items if i.saturated_fat_g is not None), 2
    )

    updated_response = MealRecommendationResponse(
        recommendation_id=rec.id,
        user_id=rec.user_id,
        meal_type=rec.meal_type,
        status="generated",
        reason_code=None,
        algorithm_version=rec.algorithm_version,
        generated_at=rec.generated_at,
        items=updated_items,
        total_energy_kcal=tot_energy,
        total_carbohydrate_g=tot_carb,
        total_protein_g=tot_protein,
        total_fat_g=tot_fat,
        total_fiber_g=tot_fiber,
        total_sodium_mg=tot_sodium,
        total_saturated_fat_g=tot_sat_fat,
        meal_balance_evaluation=meal_eval,
        safety_notes=safety_notes,
        clinical_safety_disclaimer=MealComposer.CLINICAL_DISCLAIMER,
    )

    # Persist JSONB snapshot and relational item transactionally
    rec.recommendation_result = updated_response.model_dump(mode="json")
    db_item = next(
        (it for it in rec.items if it.food_id == payload.original_food_id), None
    )
    if db_item is not None:
        db_item.food_id = new_item.food_id
        db_item.serving_multiplier = Decimal(str(new_item.serving_multiplier))
        db_item.calculated_energy_kcal = Decimal(str(new_item.energy_kcal))
        db_item.calculated_carbohydrate_g = Decimal(str(new_item.carbohydrate_g))
        db_item.calculated_protein_g = Decimal(str(new_item.protein_g))
        db_item.calculated_fat_g = Decimal(str(new_item.fat_g))
        db_item.calculated_fiber_g = Decimal(str(new_item.fiber_g or 0))
        db_item.score = Decimal(str(new_item.score))
        db_item.reason = "; ".join(new_item.reasons)

    db.commit()
    db.refresh(rec)
    return updated_response


def get_daily_recommendations(
    db: Session,
    user_id: uuid.UUID,
    target_date: Optional[date] = None,
) -> DailyRecommendationsResponse:
    """Retrieve latest recommendation per meal_type for target_date (defaults to today UTC) with daily summary."""
    day = target_date or datetime.now(timezone.utc).date()
    start_dt = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    stmt = (
        select(MealRecommendation)
        .where(
            MealRecommendation.user_id == user_id,
            MealRecommendation.generated_at >= start_dt,
            MealRecommendation.generated_at < end_dt,
        )
        .order_by(MealRecommendation.generated_at.desc())
    )
    records = list(db.scalars(stmt).all())

    latest_by_meal: Dict[str, MealRecommendationResponse] = {}
    for rec in records:
        if rec.meal_type not in latest_by_meal:
            parsed = MealRecommendationResponse.model_validate(rec.recommendation_result)
            if parsed.total_sodium_mg is None:
                parsed.total_sodium_mg = round(
                    sum(i.sodium_mg for i in parsed.items if i.sodium_mg is not None), 2
                )
            if parsed.total_saturated_fat_g is None:
                parsed.total_saturated_fat_g = round(
                    sum(i.saturated_fat_g for i in parsed.items if i.saturated_fat_g is not None),
                    2,
                )
            latest_by_meal[rec.meal_type] = parsed

    ordered_meals: List[MealRecommendationResponse] = []
    for meal_key in ("breakfast", "lunch", "dinner", "snack"):
        if meal_key in latest_by_meal:
            ordered_meals.append(latest_by_meal[meal_key])

    summary = DailyNutritionSummary(
        total_energy_kcal=round(sum(m.total_energy_kcal for m in ordered_meals), 2),
        total_carbohydrate_g=round(sum(m.total_carbohydrate_g for m in ordered_meals), 2),
        total_protein_g=round(sum(m.total_protein_g for m in ordered_meals), 2),
        total_fat_g=round(sum(m.total_fat_g for m in ordered_meals), 2),
        total_fiber_g=round(sum(m.total_fiber_g for m in ordered_meals), 2),
        total_sodium_mg=round(sum((m.total_sodium_mg or 0.0) for m in ordered_meals), 2),
        total_saturated_fat_g=round(
            sum((m.total_saturated_fat_g or 0.0) for m in ordered_meals), 2
        ),
        meals_count=len(ordered_meals),
    )

    return DailyRecommendationsResponse(
        date=day,
        user_id=user_id,
        meals=ordered_meals,
        daily_summary=summary,
    )
