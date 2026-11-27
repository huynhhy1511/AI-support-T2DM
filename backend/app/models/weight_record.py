import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class WeightRecord(Base):
    __tablename__ = "weight_records"
    __table_args__ = (
        CheckConstraint("weight_kg > 0", name="ck_weight_records_weight_positive"),
        UniqueConstraint("user_id", "recorded_at", name="uq_weight_records_user_date"),
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
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="weight_records",
    )
