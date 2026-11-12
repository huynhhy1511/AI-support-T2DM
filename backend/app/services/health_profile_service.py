import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas.health_profile import HealthProfileCreate, HealthProfileUpdate


def get_profile_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[HealthProfile]:
    """Retrieve health profile by associated user_id."""
    stmt = select(HealthProfile).where(HealthProfile.user_id == user_id)
    return db.scalars(stmt).first()


def get_profile_by_id(db: Session, profile_id: uuid.UUID) -> Optional[HealthProfile]:
    """Retrieve health profile by profile id."""
    stmt = select(HealthProfile).where(HealthProfile.id == profile_id)
    return db.scalars(stmt).first()


def create_profile(db: Session, profile_in: HealthProfileCreate) -> HealthProfile:
    """Create a new health profile for a user."""
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
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(
    db: Session, user_id: uuid.UUID, profile_in: HealthProfileUpdate
) -> Optional[HealthProfile]:
    """Update existing health profile for a user."""
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return None

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, user_id: uuid.UUID) -> bool:
    """Delete health profile by user_id."""
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True

