import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.meal_recommendation import MealRecommendation


class MealRecommendationItem(Base):
    __tablename__ = "meal_recommendation_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("foods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    serving_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default=text("1.00"),
    )
    calculated_energy_kcal: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    calculated_carbohydrate_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    calculated_protein_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    calculated_fat_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    calculated_fiber_g: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    recommendation: Mapped["MealRecommendation"] = relationship(
        "MealRecommendation",
        back_populates="items",
    )
    food: Mapped["Food"] = relationship(
        "Food",
        back_populates="recommendation_items",
    )

