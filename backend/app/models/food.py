import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.allergen import food_allergens

if TYPE_CHECKING:
    from app.models.allergen import Allergen
    from app.models.meal_recommendation_item import MealRecommendationItem


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("serving_size_g > 0", name="check_food_serving_size_positive"),
        CheckConstraint("energy_kcal >= 0", name="check_food_energy_kcal_non_negative"),
        CheckConstraint("carbohydrate_g >= 0", name="check_food_carb_non_negative"),
        CheckConstraint("protein_g >= 0", name="check_food_protein_non_negative"),
        CheckConstraint("fat_g >= 0", name="check_food_fat_non_negative"),
        CheckConstraint("fiber_g IS NULL OR fiber_g >= 0", name="check_food_fiber_non_negative"),
        CheckConstraint("sugar_g IS NULL OR sugar_g >= 0", name="check_food_sugar_non_negative"),
        CheckConstraint(
            "glycemic_index IS NULL OR (glycemic_index >= 0 AND glycemic_index <= 150)",
            name="check_food_gi_range",
        ),
        CheckConstraint("glycemic_load IS NULL OR glycemic_load >= 0", name="check_food_gl_non_negative"),
        CheckConstraint("sodium_mg IS NULL OR sodium_mg >= 0", name="ck_foods_sodium_non_negative"),
        CheckConstraint("saturated_fat_g IS NULL OR saturated_fat_g >= 0", name="ck_foods_saturated_fat_non_negative"),
        CheckConstraint(
            "preparation_state IN ('raw', 'cooked', 'ready_to_eat')",
            name="ck_foods_preparation_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    serving_size_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    energy_kcal: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    carbohydrate_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    protein_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    fat_g: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )
    fiber_g: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    sugar_g: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    glycemic_index: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    glycemic_load: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    sodium_mg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    saturated_fat_g: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    preparation_state: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="cooked",
        server_default=text("'cooked'"),
    )
    data_source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="VN_NIN_USDA",
        server_default=text("'VN_NIN_USDA'"),
    )
    data_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="v1.0",
        server_default=text("'v1.0'"),
    )
    is_test_data: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    source_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
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

    # Relationships
    allergens: Mapped[List["Allergen"]] = relationship(
        "Allergen",
        secondary=food_allergens,
        back_populates="foods",
        lazy="selectin",
    )
    recommendation_items: Mapped[List["MealRecommendationItem"]] = relationship(
        "MealRecommendationItem",
        back_populates="food",
        cascade="all, delete-orphan",
    )

