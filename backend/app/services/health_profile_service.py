import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health_profile import HealthProfile
from app.schemas.health_profile import (
    HealthProfileCompletenessResponse,
    HealthProfileCreate,
    HealthProfileUpdate,
)

REQUIRED_COMPLETENESS_FIELDS = (
    "date_of_birth",
    "sex",
    "height_cm",
    "weight_kg",
    "activity_level",
)


def calculate_bmi(
    height_cm: Optional[Decimal | float],
    weight_kg: Optional[Decimal | float],
) -> Optional[float]:
    """Calculate BMI = weight_kg / (height_m ^ 2) rounded to 2 decimals."""
    if height_cm is None or weight_kg is None:
        return None
    h = float(height_cm)
    w = float(weight_kg)
    if h <= 0 or w <= 0:
        return None
    height_m = h / 100.0
    return round(w / (height_m * height_m), 2)


def _clean_string_list(items: Optional[List[str]]) -> List[str]:
    if not items:
        return []
    seen = set()
    cleaned: List[str] = []
    for raw in items:
        if not isinstance(raw, str):
            continue
        val = raw.strip()
        if not val:
            continue
        key = val.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(val)
    return cleaned


class EnergyCalculator:
    """Calculates BMR, TDEE, and safe daily target energy using the Mifflin-St Jeor equation."""

    ACTIVITY_FACTORS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    WEIGHT_LOSS_DEFICIT_KCAL = 400.0

    @staticmethod
    def _calculate_age(dob: date, reference_date: Optional[date] = None) -> int:
        today = reference_date or date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return max(1, age)

    @classmethod
    def calculate(
        cls,
        date_of_birth: Optional[date],
        sex: Optional[str],
        height_cm: Optional[Decimal | float],
        weight_kg: Optional[Decimal | float],
        activity_level: Optional[str],
        nutrition_goal: str = "maintenance",
        reference_date: Optional[date] = None,
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Return (bmr_kcal, tdee_kcal, target_energy_kcal) or (None, None, None) if inputs incomplete."""
        if (
            date_of_birth is None
            or not sex
            or height_cm is None
            or weight_kg is None
            or not activity_level
        ):
            return None, None, None

        h = float(height_cm)
        w = float(weight_kg)
        if h <= 0 or w <= 0:
            return None, None, None

        sex_norm = sex.lower().strip()
        act_norm = activity_level.lower().strip()
        factor = cls.ACTIVITY_FACTORS.get(act_norm)
        if factor is None:
            return None, None, None

        age = cls._calculate_age(date_of_birth, reference_date=reference_date)

        # Mifflin-St Jeor BMR
        if sex_norm == "male":
            bmr = 10.0 * w + 6.25 * h - 5.0 * age + 5.0
            floor_kcal = 1400.0
        elif sex_norm == "female":
            bmr = 10.0 * w + 6.25 * h - 5.0 * age - 161.0
            floor_kcal = 1200.0
        else:
            bmr = 10.0 * w + 6.25 * h - 5.0 * age - 78.0
            floor_kcal = 1300.0

        bmr = max(500.0, bmr)
        tdee = bmr * factor

        bmi = calculate_bmi(h, w)
        goal_norm = (nutrition_goal or "maintenance").lower().strip()
        if goal_norm == "weight_loss" and (bmi is None or bmi >= 18.5):
            target = max(floor_kcal, tdee - cls.WEIGHT_LOSS_DEFICIT_KCAL)
        else:
            target = max(floor_kcal, tdee)

        return round(bmr, 1), round(tdee, 1), round(target, 1)

    @classmethod
    def apply_to_profile(cls, profile: HealthProfile) -> None:
        bmr, tdee, target = cls.calculate(
            date_of_birth=profile.date_of_birth,
            sex=profile.sex,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level,
            nutrition_goal=profile.nutrition_goal or "maintenance",
        )
        profile.bmr_kcal = bmr
        profile.tdee_kcal = tdee
        profile.target_energy_kcal = target


def get_profile_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[HealthProfile]:
    """Retrieve health profile by associated user_id."""
    stmt = select(HealthProfile).where(HealthProfile.user_id == user_id)
    return db.scalars(stmt).first()


def get_profile_by_id(db: Session, profile_id: uuid.UUID) -> Optional[HealthProfile]:
    """Retrieve health profile by profile id."""
    stmt = select(HealthProfile).where(HealthProfile.id == profile_id)
    return db.scalars(stmt).first()


def create_profile(db: Session, profile_in: HealthProfileCreate) -> HealthProfile:
    """Create a new health profile for a user and compute BMR/TDEE/target_energy_kcal."""
    profile = HealthProfile(
        user_id=profile_in.user_id,
        date_of_birth=profile_in.date_of_birth,
        sex=profile_in.sex,
        height_cm=profile_in.height_cm,
        weight_kg=profile_in.weight_kg,
        diabetes_type=profile_in.diabetes_type or "type2",
        diagnosis_year=profile_in.diagnosis_year,
        activity_level=profile_in.activity_level,
        dietary_preference=profile_in.dietary_preference,
        nutrition_goal=profile_in.nutrition_goal or "maintenance",
        comorbidities=_clean_string_list(profile_in.comorbidities),
        allergies=_clean_string_list(profile_in.allergies),
    )
    EnergyCalculator.apply_to_profile(profile)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(
    db: Session, user_id: uuid.UUID, profile_in: HealthProfileUpdate
) -> Optional[HealthProfile]:
    """Update existing health profile for a user and recompute energy targets."""
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return None

    update_data = profile_in.model_dump(exclude_unset=True)
    if "comorbidities" in update_data:
        update_data["comorbidities"] = _clean_string_list(update_data["comorbidities"])
    if "allergies" in update_data:
        update_data["allergies"] = _clean_string_list(update_data["allergies"])

    for field, value in update_data.items():
        setattr(profile, field, value)

    EnergyCalculator.apply_to_profile(profile)
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


def upsert_profile_for_user(
    db: Session, user_id: uuid.UUID, profile_in: HealthProfileUpdate
) -> HealthProfile:
    """Create health profile if missing, otherwise update existing profile."""
    existing = get_profile_by_user_id(db, user_id)
    if existing is not None:
        updated = update_profile(db, user_id, profile_in)
        assert updated is not None
        return updated

    data = profile_in.model_dump(exclude_unset=True)
    create_payload = HealthProfileCreate(
        user_id=user_id,
        date_of_birth=data.get("date_of_birth"),
        sex=data.get("sex"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        diabetes_type=data.get("diabetes_type") or "type2",
        diagnosis_year=data.get("diagnosis_year"),
        activity_level=data.get("activity_level"),
        dietary_preference=data.get("dietary_preference"),
        nutrition_goal=data.get("nutrition_goal") or "maintenance",
        comorbidities=data.get("comorbidities") or [],
        allergies=data.get("allergies") or [],
    )
    return create_profile(db, create_payload)


def compute_profile_completeness(
    profile: Optional[HealthProfile],
) -> HealthProfileCompletenessResponse:
    """Evaluate profile completeness, missing anthropometric fields, BMI, and energy targets."""
    if profile is None:
        return HealthProfileCompletenessResponse(
            is_complete=False,
            missing_fields=list(REQUIRED_COMPLETENESS_FIELDS),
            bmi=None,
            bmr_kcal=None,
            tdee_kcal=None,
            target_energy_kcal=None,
        )

    missing = [
        field for field in REQUIRED_COMPLETENESS_FIELDS if getattr(profile, field) is None
    ]
    bmi = calculate_bmi(profile.height_cm, profile.weight_kg)
    bmr, tdee, target = (
        profile.bmr_kcal,
        profile.tdee_kcal,
        profile.target_energy_kcal,
    )
    if not missing and target is None:
        bmr, tdee, target = EnergyCalculator.calculate(
            date_of_birth=profile.date_of_birth,
            sex=profile.sex,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level,
            nutrition_goal=profile.nutrition_goal or "maintenance",
        )

    return HealthProfileCompletenessResponse(
        is_complete=(len(missing) == 0),
        missing_fields=missing,
        bmi=bmi,
        bmr_kcal=bmr,
        tdee_kcal=tdee,
        target_energy_kcal=target,
    )


def delete_profile(db: Session, user_id: uuid.UUID) -> bool:
    """Delete health profile by user_id."""
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True
