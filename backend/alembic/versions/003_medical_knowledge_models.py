"""create medical knowledge and medical sources models

Revision ID: 003_medical_knowledge_models
Revises: 002_nutrition_models
Create Date: 2026-11-25 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_medical_knowledge_models"
down_revision: Union[str, None] = "002_nutrition_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'medical_sources' table
    op.create_table(
        "medical_sources",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("organization", sa.String(length=100), nullable=False),
        sa.Column("document_name", sa.String(length=255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("section_page", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="medical_sources_pkey"),
    )

    # 2. Create 'medical_knowledges' table
    op.create_table(
        "medical_knowledges",
        sa.Column("entry_id", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("subtopic", sa.String(length=150), nullable=False),
        sa.Column("population", sa.String(length=150), nullable=True),
        sa.Column("knowledge", sa.Text(), nullable=False),
        sa.Column("evidence_grade", sa.String(length=10), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=False),
        sa.Column("recommendation_en", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["medical_sources.id"],
            name="medical_knowledges_source_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("entry_id", name="medical_knowledges_pkey"),
    )
    op.create_index("ix_medical_knowledges_topic", "medical_knowledges", ["topic"])
    op.create_index("ix_medical_knowledges_subtopic", "medical_knowledges", ["subtopic"])
    op.create_index("ix_medical_knowledges_source_id", "medical_knowledges", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_medical_knowledges_source_id", table_name="medical_knowledges")
    op.drop_index("ix_medical_knowledges_subtopic", table_name="medical_knowledges")
    op.drop_index("ix_medical_knowledges_topic", table_name="medical_knowledges")
    op.drop_table("medical_knowledges")
    op.drop_table("medical_sources")
