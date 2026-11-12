import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.glucose_record import GlucoseRecord
from app.schemas.glucose_record import GlucoseRecordCreate, GlucoseRecordUpdate


def get_glucose_record_by_id(
    db: Session, record_id: uuid.UUID
) -> Optional[GlucoseRecord]:
    """Retrieve a single glucose record by id."""
    stmt = select(GlucoseRecord).where(GlucoseRecord.id == record_id)
    return db.scalars(stmt).first()


def list_glucose_records(
    db: Session,
    user_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    context: Optional[str] = None,
    unit: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[GlucoseRecord]:
    """Retrieve glucose records for a user with optional filtering and pagination."""
    stmt = select(GlucoseRecord).where(GlucoseRecord.user_id == user_id)

    if start_time:
        stmt = stmt.where(GlucoseRecord.measured_at >= start_time)
    if end_time:
        stmt = stmt.where(GlucoseRecord.measured_at <= end_time)
    if context:
        stmt = stmt.where(GlucoseRecord.measurement_context == context)
    if unit:
        stmt = stmt.where(GlucoseRecord.unit == unit)

    stmt = stmt.order_by(GlucoseRecord.measured_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_glucose_record(
    db: Session, record_in: GlucoseRecordCreate
) -> GlucoseRecord:
    """Create a new blood glucose record."""
    measured_time = record_in.measured_at or datetime.now(timezone.utc)
    record = GlucoseRecord(
        user_id=record_in.user_id,
        measured_at=measured_time,
        glucose_value=record_in.glucose_value,
        unit=record_in.unit,
        measurement_context=record_in.measurement_context,
        note=record_in.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_glucose_record(
    db: Session, record_id: uuid.UUID, record_in: GlucoseRecordUpdate
) -> Optional[GlucoseRecord]:
    """Update an existing glucose record."""
    record = get_glucose_record_by_id(db, record_id)
    if not record:
        return None

    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_glucose_record(db: Session, record_id: uuid.UUID) -> bool:
    """Delete a glucose record by id."""
    record = get_glucose_record_by_id(db, record_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_glucose_statistics(
    db: Session, user_id: uuid.UUID, unit: str = "mmol/L"
) -> dict:
    """Calculate summary statistics (count, avg, min, max) for a user's glucose records."""
    stmt = (
        select(
            func.count(GlucoseRecord.id).label("count"),
            func.avg(GlucoseRecord.glucose_value).label("avg_value"),
            func.min(GlucoseRecord.glucose_value).label("min_value"),
            func.max(GlucoseRecord.glucose_value).label("max_value"),
        )
        .where(GlucoseRecord.user_id == user_id)
        .where(GlucoseRecord.unit == unit)
    )
    result = db.execute(stmt).first()
    if not result or result.count == 0:
        return {
            "user_id": user_id,
            "count": 0,
            "avg_value": None,
            "min_value": None,
            "max_value": None,
            "unit": unit,
        }

    return {
        "user_id": user_id,
        "count": result.count,
        "avg_value": round(float(result.avg_value), 2) if result.avg_value is not None else None,
        "min_value": round(float(result.min_value), 2) if result.min_value is not None else None,
        "max_value": round(float(result.max_value), 2) if result.max_value is not None else None,
        "unit": unit,
    }

