from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MedicalSource(Base):
    __tablename__ = "medical_sources"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    organization: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    document_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    section_page: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    knowledges: Mapped[List["MedicalKnowledge"]] = relationship(
        "MedicalKnowledge",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class MedicalKnowledge(Base):
    __tablename__ = "medical_knowledges"

    entry_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    subtopic: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    population: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    knowledge: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence_grade: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("medical_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    recommendation_en: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    source: Mapped["MedicalSource"] = relationship(
        "MedicalSource",
        back_populates="knowledges",
    )
