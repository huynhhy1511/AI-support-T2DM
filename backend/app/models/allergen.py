import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.food import Food


food_allergens = Table(
    "food_allergens",
    Base.metadata,
    Column(
        "food_id",
        UUID(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "allergen_id",
        UUID(as_uuid=True),
        ForeignKey("allergens.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    name_vi: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    foods: Mapped[List["Food"]] = relationship(
        "Food",
        secondary=food_allergens,
        back_populates="allergens",
    )
