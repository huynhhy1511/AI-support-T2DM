import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.meal_recommendation_item import MealRecommendationItem
    from app.models.user import User


class MealRecommendation(Base):
    __tablename__ = "meal_recommendations"

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
    meal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    algorithm_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1.0-rule_scoring",
        server_default=text("'v1.0-rule_scoring'"),
    )
    input_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    recommendation_result: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="meal_recommendations",
    )
    items: Mapped[List["MealRecommendationItem"]] = relationship(
        "MealRecommendationItem",
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )

