"""add clinical nutrition fields and energy targets to health_profiles

Revision ID: 005_health_profile_clinical_fields
Revises: 004_food_metadata_and_allergens
Create Date: 2026-11-27 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "005_health_profile_clinical"
down_revision: Union[str, None] = "004_food_metadata_and_allergens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "health_profiles",
        sa.Column(
            "nutrition_goal",
            sa.String(length=30),
            nullable=False,
            server_default="maintenance",
        ),
    )
    op.add_column(
        "health_profiles",
        sa.Column(
            "comorbidities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "health_profiles",
        sa.Column(
            "allergies",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "health_profiles",
        sa.Column("bmr_kcal", sa.Float(), nullable=True),
    )
    op.add_column(
        "health_profiles",
        sa.Column("tdee_kcal", sa.Float(), nullable=True),
    )
    op.add_column(
        "health_profiles",
        sa.Column("target_energy_kcal", sa.Float(), nullable=True),
    )

    op.create_check_constraint(
        "ck_health_profiles_nutrition_goal",
        "health_profiles",
        "nutrition_goal IN ('weight_loss', 'maintenance')",
    )
    op.create_check_constraint(
        "ck_health_profiles_bmr_positive",
        "health_profiles",
        "bmr_kcal IS NULL OR bmr_kcal > 0",
    )
    op.create_check_constraint(
        "ck_health_profiles_tdee_positive",
        "health_profiles",
        "tdee_kcal IS NULL OR tdee_kcal > 0",
    )
    op.create_check_constraint(
        "ck_health_profiles_target_energy_positive",
        "health_profiles",
        "target_energy_kcal IS NULL OR target_energy_kcal > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_health_profiles_target_energy_positive", "health_profiles", type_="check")
    op.drop_constraint("ck_health_profiles_tdee_positive", "health_profiles", type_="check")
    op.drop_constraint("ck_health_profiles_bmr_positive", "health_profiles", type_="check")
    op.drop_constraint("ck_health_profiles_nutrition_goal", "health_profiles", type_="check")
    op.drop_column("health_profiles", "target_energy_kcal")
    op.drop_column("health_profiles", "tdee_kcal")
    op.drop_column("health_profiles", "bmr_kcal")
    op.drop_column("health_profiles", "allergies")
    op.drop_column("health_profiles", "comorbidities")
    op.drop_column("health_profiles", "nutrition_goal")
