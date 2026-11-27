import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.meal_recommendation import MealRecommendation
    from app.models.user import User


class MealLog(Base):
    __tablename__ = "meal_logs"
    __table_args__ = (
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meal_logs_meal_type",
        ),
        CheckConstraint(
            "status IN ('eaten', 'partially_eaten', 'skipped', 'eaten_other')",
            name="ck_meal_logs_status",
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
    recommendation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    meal_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    meal_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="meal_logs",
    )
    recommendation: Mapped[Optional["MealRecommendation"]] = relationship(
        "MealRecommendation",
    )
    items: Mapped[List["MealLogItem"]] = relationship(
        "MealLogItem",
        back_populates="meal_log",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MealLogItem(Base):
    __tablename__ = "meal_log_items"
    __table_args__ = (
        CheckConstraint("serving_g > 0", name="ck_meal_log_items_serving_positive"),
        CheckConstraint("calories_kcal >= 0", name="ck_meal_log_items_calories_non_negative"),
        CheckConstraint("carbs_g >= 0", name="ck_meal_log_items_carbs_non_negative"),
        CheckConstraint("protein_g >= 0", name="ck_meal_log_items_protein_non_negative"),
        CheckConstraint("fat_g >= 0", name="ck_meal_log_items_fat_non_negative"),
        CheckConstraint(
            "fiber_g IS NULL OR fiber_g >= 0",
            name="ck_meal_log_items_fiber_non_negative",
        ),
        CheckConstraint(
            "sodium_mg IS NULL OR sodium_mg >= 0",
            name="ck_meal_log_items_sodium_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    meal_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("foods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    custom_food_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    serving_g: Mapped[float] = mapped_column(Float, nullable=False)
    calories_kcal: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    meal_log: Mapped["MealLog"] = relationship(
        "MealLog",
        back_populates="items",
    )
    food: Mapped[Optional["Food"]] = relationship(
        "Food",
        lazy="selectin",
    )
