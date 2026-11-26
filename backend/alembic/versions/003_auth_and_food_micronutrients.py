"""add password_hash to users and sodium_mg, saturated_fat_g to foods

Revision ID: 003_auth_and_food_micronutrients
Revises: 002_nutrition_models
Create Date: 2026-11-26 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_auth_and_food_micronutrients"
down_revision: Union[str, None] = "002_nutrition_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add password_hash to users
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )

    # 2. Add sodium_mg and saturated_fat_g to foods with non-negative check constraints
    op.add_column(
        "foods",
        sa.Column("sodium_mg", sa.Float(), nullable=True),
    )
    op.add_column(
        "foods",
        sa.Column("saturated_fat_g", sa.Float(), nullable=True),
    )
    op.create_check_constraint(
        "ck_foods_sodium_non_negative",
        "foods",
        "sodium_mg IS NULL OR sodium_mg >= 0",
    )
    op.create_check_constraint(
        "ck_foods_saturated_fat_non_negative",
        "foods",
        "saturated_fat_g IS NULL OR saturated_fat_g >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_foods_saturated_fat_non_negative", "foods", type_="check")
    op.drop_constraint("ck_foods_sodium_non_negative", "foods", type_="check")
    op.drop_column("foods", "saturated_fat_g")
    op.drop_column("foods", "sodium_mg")
    op.drop_column("users", "password_hash")
