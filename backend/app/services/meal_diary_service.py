import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meal_log import MealLog, MealLogItem
from app.models.meal_recommendation import MealRecommendation
from app.models.weight_record import WeightRecord
from app.schemas.meal_diary import (
    ActualNutritionSummary,
    MealLogCreate,
    MealLogItemCreate,
    MealLogItemResponse,
    MealLogListResponse,
    MealLogResponse,
    MealLogUpdate,
    NutritionProgressResponse,
    NutritionTrendPoint,
    ProgressPeriod,
    ProgressSummary,
    WeightProgressSummary,
    WeightRecordCreate,
    WeightRecordResponse,
)
from app.schemas.nutrition import MealRecommendationResponse
from app.services.food_service import get_food_by_id
from app.services.health_profile_service import (
    EnergyCalculator,
    get_profile_by_user_id,
)


def _build_meal_log_items(
    db: Session, item_inputs: List[MealLogItemCreate]
) -> List[MealLogItem]:
    """Compute item nutrition snapshots strictly on the backend from Food DB or custom entry."""
    built: List[MealLogItem] = []
    for item in item_inputs:
        if item.food_id is not None:
            food = get_food_by_id(db, item.food_id)
            if not food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food with id '{item.food_id}' not found.",
                )
            ratio = item.serving_g / float(food.serving_size_g)
            calories = round(float(food.energy_kcal) * ratio, 2)
            carbs = round(float(food.carbohydrate_g) * ratio, 2)
            protein = round(float(food.protein_g) * ratio, 2)
            fat = round(float(food.fat_g) * ratio, 2)
            fiber = (
                round(float(food.fiber_g) * ratio, 2)
                if food.fiber_g is not None
                else None
            )
            sodium = (
                round(float(food.sodium_mg) * ratio, 2)
                if food.sodium_mg is not None
                else None
            )
            custom_name = (
                item.custom_food_name.strip() if item.custom_food_name else None
            )
        else:
            calories = round(float(item.calories_kcal or 0.0), 2)
            carbs = round(float(item.carbs_g or 0.0), 2)
            protein = round(float(item.protein_g or 0.0), 2)
            fat = round(float(item.fat_g or 0.0), 2)
            fiber = round(float(item.fiber_g), 2) if item.fiber_g is not None else None
            sodium = (
                round(float(item.sodium_mg), 2)
                if item.sodium_mg is not None
                else None
            )
            custom_name = item.custom_food_name.strip() if item.custom_food_name else None

        built.append(
            MealLogItem(
                food_id=item.food_id,
                custom_food_name=custom_name,
                serving_g=round(item.serving_g, 2),
                calories_kcal=calories,
                carbs_g=carbs,
                protein_g=protein,
                fat_g=fat,
                fiber_g=fiber,
                sodium_mg=sodium,
            )
        )
    return built


def _summarize_actual_nutrition(items: List[MealLogItem]) -> ActualNutritionSummary:
    if not items:
        return ActualNutritionSummary(
            calories_kcal=0.0,
            carbs_g=0.0,
            protein_g=0.0,
            fat_g=0.0,
            fiber_g=None,
            sodium_mg=None,
        )

    fiber_vals = [it.fiber_g for it in items if it.fiber_g is not None]
    sodium_vals = [it.sodium_mg for it in items if it.sodium_mg is not None]

    return ActualNutritionSummary(
        calories_kcal=round(sum(it.calories_kcal for it in items), 2),
        carbs_g=round(sum(it.carbs_g for it in items), 2),
        protein_g=round(sum(it.protein_g for it in items), 2),
        fat_g=round(sum(it.fat_g for it in items), 2),
        fiber_g=round(sum(fiber_vals), 2) if fiber_vals else None,
        sodium_mg=round(sum(sodium_vals), 2) if sodium_vals else None,
    )


def _serialize_meal_log(log: MealLog) -> MealLogResponse:
    serialized_items = [
        MealLogItemResponse(
            id=it.id,
            food_id=it.food_id,
            food_name=it.food.name if it.food is not None else it.custom_food_name,
            custom_food_name=it.custom_food_name,
            serving_g=it.serving_g,
            calories_kcal=it.calories_kcal,
            carbs_g=it.carbs_g,
            protein_g=it.protein_g,
            fat_g=it.fat_g,
            fiber_g=it.fiber_g,
            sodium_mg=it.sodium_mg,
        )
        for it in log.items
    ]
    return MealLogResponse(
        id=log.id,
        user_id=log.user_id,
        recommendation_id=log.recommendation_id,
        meal_date=log.meal_date,
        meal_type=log.meal_type,
        status=log.status,
        notes=log.notes,
        items=serialized_items,
        actual_nutrition=_summarize_actual_nutrition(log.items),
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


def _get_owned_meal_log(
    db: Session, log_id: uuid.UUID, current_user_id: uuid.UUID
) -> MealLog:
    log = db.get(MealLog, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal log '{log_id}' not found.",
        )
    if log.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this meal log.",
        )
    return log


def create_meal_log(
    db: Session, user_id: uuid.UUID, payload: MealLogCreate
) -> MealLogResponse:
    """Create a meal diary entry with backend-computed item nutrition without mutating recommendations."""
    if payload.recommendation_id is not None:
        rec = db.get(MealRecommendation, payload.recommendation_id)
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal recommendation '{payload.recommendation_id}' not found.",
            )
        if rec.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot link a meal log to another user's recommendation.",
            )

    items = _build_meal_log_items(db, payload.items)
    log = MealLog(
        user_id=user_id,
        recommendation_id=payload.recommendation_id,
        meal_date=payload.meal_date,
        meal_type=payload.meal_type,
        status=payload.status,
        notes=payload.notes,
        items=items,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _serialize_meal_log(log)


def list_meal_logs(
    db: Session,
    user_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    meal_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> MealLogListResponse:
    """List user meal logs with date range, meal_type filters and pagination."""
    conditions = [MealLog.user_id == user_id]
    if date_from is not None:
        conditions.append(MealLog.meal_date >= date_from)
    if date_to is not None:
        conditions.append(MealLog.meal_date <= date_to)
    if meal_type is not None:
        conditions.append(MealLog.meal_type == meal_type)

    total = db.scalar(select(func.count(MealLog.id)).where(*conditions)) or 0
    offset = (page - 1) * page_size
    stmt = (
        select(MealLog)
        .where(*conditions)
        .order_by(MealLog.meal_date.desc(), MealLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = list(db.scalars(stmt).all())
    return MealLogListResponse(
        items=[_serialize_meal_log(row) for row in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


def get_meal_log(
    db: Session, log_id: uuid.UUID, user_id: uuid.UUID
) -> MealLogResponse:
    log = _get_owned_meal_log(db, log_id, user_id)
    return _serialize_meal_log(log)


def update_meal_log(
    db: Session, log_id: uuid.UUID, user_id: uuid.UUID, payload: MealLogUpdate
) -> MealLogResponse:
    log = _get_owned_meal_log(db, log_id, user_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and payload.status is not None:
        log.status = payload.status
    if "notes" in update_data:
        log.notes = payload.notes
    if "items" in update_data and payload.items is not None:
        new_items = _build_meal_log_items(db, payload.items)
        log.items.clear()
        db.flush()
        log.items.extend(new_items)

    log.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(log)
    return _serialize_meal_log(log)


def delete_meal_log(db: Session, log_id: uuid.UUID, user_id: uuid.UUID) -> None:
    log = _get_owned_meal_log(db, log_id, user_id)
    db.delete(log)
    db.commit()


def upsert_weight_record(
    db: Session, user_id: uuid.UUID, payload: WeightRecordCreate
) -> WeightRecord:
    """Upsert weight record per (user_id, recorded_at) and sync latest weight to HealthProfile."""
    stmt = select(WeightRecord).where(
        WeightRecord.user_id == user_id,
        WeightRecord.recorded_at == payload.recorded_at,
    )
    record = db.scalars(stmt).first()
    rounded_weight = round(payload.weight_kg, 2)

    if record is None:
        record = WeightRecord(
            user_id=user_id,
            weight_kg=rounded_weight,
            recorded_at=payload.recorded_at,
        )
        db.add(record)
    else:
        record.weight_kg = rounded_weight

    db.flush()

    # Sync the chronologically latest weight to HealthProfile and recompute BMR/TDEE/target
    latest_weight_rec = db.scalars(
        select(WeightRecord)
        .where(WeightRecord.user_id == user_id)
        .order_by(WeightRecord.recorded_at.desc())
        .limit(1)
    ).first()
    profile = get_profile_by_user_id(db, user_id)
    if profile is not None and latest_weight_rec is not None:
        profile.weight_kg = Decimal(str(round(latest_weight_rec.weight_kg, 2)))
        EnergyCalculator.apply_to_profile(profile)
        profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)
    return record


def list_weight_records(
    db: Session,
    user_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[WeightRecord]:
    conditions = [WeightRecord.user_id == user_id]
    if date_from is not None:
        conditions.append(WeightRecord.recorded_at >= date_from)
    if date_to is not None:
        conditions.append(WeightRecord.recorded_at <= date_to)

    stmt = (
        select(WeightRecord)
        .where(*conditions)
        .order_by(WeightRecord.recorded_at.asc())
    )
    return list(db.scalars(stmt).all())


def get_nutrition_progress(
    db: Session,
    user_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> NutritionProgressResponse:
    """Aggregate adherence, planned-vs-actual nutrition trends, and weight history for period."""
    end_day = date_to or datetime.now(timezone.utc).date()
    start_day = date_from or (end_day - timedelta(days=29))

    if start_day > end_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be less than or equal to date_to.",
        )

    # 1. Aggregate actual meal logs
    logs_stmt = (
        select(MealLog)
        .where(
            MealLog.user_id == user_id,
            MealLog.meal_date >= start_day,
            MealLog.meal_date <= end_day,
        )
        .order_by(MealLog.meal_date.asc())
    )
    logs = list(db.scalars(logs_stmt).all())

    total_meals_skipped = 0
    total_meals_logged = 0
    actual_by_day: Dict[date, Dict[str, float]] = {}

    for log in logs:
        if log.status == "skipped":
            total_meals_skipped += 1
        else:
            total_meals_logged += 1

        bucket = actual_by_day.setdefault(log.meal_date, {"kcal": 0.0, "carbs": 0.0})
        if log.status != "skipped":
            bucket["kcal"] += sum(it.calories_kcal for it in log.items)
            bucket["carbs"] += sum(it.carbs_g for it in log.items)

    total_tracked = total_meals_logged + total_meals_skipped
    logging_rate = (
        round(total_meals_logged / total_tracked, 4) if total_tracked > 0 else 0.0
    )

    # 2. Aggregate planned meals (latest recommendation per (day, meal_type))
    start_dt = datetime(start_day.year, start_day.month, start_day.day, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(end_day.year, end_day.month, end_day.day, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=1)

    recs_stmt = (
        select(MealRecommendation)
        .where(
            MealRecommendation.user_id == user_id,
            MealRecommendation.generated_at >= start_dt,
            MealRecommendation.generated_at < end_dt,
        )
        .order_by(MealRecommendation.generated_at.desc())
    )
    recs = list(db.scalars(recs_stmt).all())

    latest_planned: Dict[tuple, MealRecommendationResponse] = {}
    for rec in recs:
        rec_day = rec.generated_at.astimezone(timezone.utc).date()
        key = (rec_day, rec.meal_type)
        if key not in latest_planned:
            latest_planned[key] = MealRecommendationResponse.model_validate(
                rec.recommendation_result
            )

    planned_by_day: Dict[date, Dict[str, float]] = {}
    for (rec_day, _), rec_resp in latest_planned.items():
        bucket = planned_by_day.setdefault(rec_day, {"kcal": 0.0, "carbs": 0.0})
        bucket["kcal"] += rec_resp.total_energy_kcal
        bucket["carbs"] += rec_resp.total_carbohydrate_g

    all_dates = sorted(set(planned_by_day.keys()) | set(actual_by_day.keys()))
    trends = [
        NutritionTrendPoint(
            date=d,
            planned_calories_kcal=round(planned_by_day.get(d, {}).get("kcal", 0.0), 2),
            actual_calories_kcal=round(actual_by_day.get(d, {}).get("kcal", 0.0), 2),
            planned_carbs_g=round(planned_by_day.get(d, {}).get("carbs", 0.0), 2),
            actual_carbs_g=round(actual_by_day.get(d, {}).get("carbs", 0.0), 2),
        )
        for d in all_dates
    ]

    # 3. Weight records in range
    weight_rows = list_weight_records(db, user_id, date_from=start_day, date_to=end_day)
    latest_kg = weight_rows[-1].weight_kg if len(weight_rows) >= 1 else None
    previous_kg = weight_rows[-2].weight_kg if len(weight_rows) >= 2 else None

    return NutritionProgressResponse(
        period=ProgressPeriod(date_from=start_day, date_to=end_day),
        summary=ProgressSummary(
            total_meals_logged=total_meals_logged,
            total_meals_skipped=total_meals_skipped,
            meal_logging_rate=logging_rate,
        ),
        nutrition_trends=trends,
        weight=WeightProgressSummary(
            latest_kg=latest_kg,
            previous_kg=previous_kg,
            records=[WeightRecordResponse.model_validate(w) for w in weight_rows],
        ),
    )
