import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    sex: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    height_cm: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    diabetes_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="type2",
        server_default=text("'type2'"),
    )
    diagnosis_year: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    activity_level: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    dietary_preference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="health_profile",
    )
