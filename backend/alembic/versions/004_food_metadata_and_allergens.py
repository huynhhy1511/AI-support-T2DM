"""add food metadata columns and normalized allergens tables

Revision ID: 004_food_metadata_and_allergens
Revises: 003_auth_and_food_micronutrients
Create Date: 2026-11-27 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "004_food_metadata_and_allergens"
down_revision: Union[str, None] = "003_auth_and_food_micronutrients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add TV3 standardization metadata columns to foods
    op.add_column(
        "foods",
        sa.Column(
            "preparation_state",
            sa.String(length=30),
            nullable=False,
            server_default="cooked",
        ),
    )
    op.add_column(
        "foods",
        sa.Column(
            "data_source",
            sa.String(length=100),
            nullable=False,
            server_default="VN_NIN_USDA",
        ),
    )
    op.add_column(
        "foods",
        sa.Column(
            "data_version",
            sa.String(length=30),
            nullable=False,
            server_default="v1.0",
        ),
    )
    op.create_check_constraint(
        "ck_foods_preparation_state",
        "foods",
        "preparation_state IN ('raw', 'cooked', 'ready_to_eat')",
    )

    # 2. Create normalized allergens table
    op.create_table(
        "allergens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name_vi", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("code", name="uq_allergens_code"),
    )
    op.create_index("ix_allergens_code", "allergens", ["code"], unique=True)

    # 3. Create food_allergens many-to-many join table
    op.create_table(
        "food_allergens",
        sa.Column(
            "food_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "allergen_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("allergens.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("food_allergens")
    op.drop_index("ix_allergens_code", table_name="allergens")
    op.drop_table("allergens")
    op.drop_constraint("ck_foods_preparation_state", "foods", type_="check")
    op.drop_column("foods", "data_version")
    op.drop_column("foods", "data_source")
    op.drop_column("foods", "preparation_state")
