import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.db.session import SessionLocal, engine
from app.models.glucose_record import GlucoseRecord
from app.models.health_profile import HealthProfile
from app.models.user import User

logger = logging.getLogger(__name__)


def test_models_in_memory_relationships():
    """Verify that User, HealthProfile, and GlucoseRecord relationships work properly."""
    user = User(
        id=uuid.uuid4(),
        email="patient@example.com",
        display_name="Nguyen Van A",
        consent_accepted_at=datetime.now(timezone.utc),
    )

    profile = HealthProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        date_of_birth=date(1980, 5, 15),
        sex="male",
        height_cm=Decimal("170.5"),
        weight_kg=Decimal("68.2"),
        diabetes_type="type2",
        diagnosis_year=2021,
        activity_level="moderate",
        dietary_preference="low-carb",
        user=user,
    )

    record1 = GlucoseRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        measured_at=datetime.now(timezone.utc),
        glucose_value=Decimal("6.50"),
        unit="mmol/L",
        measurement_context="fasting",
        note="Morning measurement",
        user=user,
    )

    record2 = GlucoseRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        measured_at=datetime.now(timezone.utc),
        glucose_value=Decimal("8.20"),
        unit="mmol/L",
        measurement_context="after_meal",
        note="2 hours post-breakfast",
        user=user,
    )

    # 1:1 relationship assertions
    assert user.health_profile is profile
    assert profile.user is user
    assert profile.diabetes_type == "type2"

    # 1:N relationship assertions
    assert len(user.glucose_records) == 2
    assert record1 in user.glucose_records
    assert record2 in user.glucose_records
    assert record1.user is user
    assert record2.user is user
    assert record1.glucose_value > 0
    assert record1.unit in ("mmol/L", "mg/dL")


def test_models_database_persistence_if_connected():
    """Verify database persistence and foreign keys if database is accessible."""
    try:
        with engine.connect() as conn:
            pass
    except OperationalError as exc:
        logger.info(
            "Database persistence test skipped: PostgreSQL not yet connected with active credentials (%s)",
            exc,
        )
        return

    # If database is connected, test transaction and rollback
    db = SessionLocal()
    try:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id.hex[:8]}@example.com",
            display_name="Test User",
        )
        db.add(user)
        db.flush()

        profile = HealthProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            diabetes_type="type2",
        )
        db.add(profile)

        record = GlucoseRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            measured_at=datetime.now(timezone.utc),
            glucose_value=Decimal("5.80"),
            unit="mmol/L",
            measurement_context="fasting",
        )
        db.add(record)
        db.flush()

        # Query back
        queried_user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one()
        assert queried_user.health_profile is not None
        assert len(queried_user.glucose_records) == 1
        assert queried_user.glucose_records[0].glucose_value == Decimal("5.80")
    finally:
        db.rollback()
        db.close()
