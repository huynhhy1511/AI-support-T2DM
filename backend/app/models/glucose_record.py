import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class GlucoseRecord(Base):
    __tablename__ = "glucose_records"
    __table_args__ = (
        CheckConstraint("glucose_value > 0", name="check_glucose_value_positive"),
        CheckConstraint(
            "unit IN ('mmol/L', 'mg/dL')",
            name="check_glucose_unit_valid",
        ),
        CheckConstraint(
            "measurement_context IS NULL OR measurement_context IN ('fasting', 'before_meal', 'after_meal', 'random', 'other')",
            name="check_glucose_measurement_context_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    glucose_value: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="mmol/L",
        server_default=text("'mmol/L'"),
    )
    measurement_context: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="glucose_records",
    )
