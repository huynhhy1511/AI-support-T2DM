"""create nutrition foods and meal recommendations models

Revision ID: 002_nutrition_models
Revises: 001_core_models
Create Date: 2026-11-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_nutrition_models"
down_revision: Union[str, None] = "001_core_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'foods' table
    op.create_table(
        "foods",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("serving_size_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("energy_kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("carbohydrate_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column(
            "fiber_g",
            sa.Numeric(precision=7, scale=2),
            server_default=sa.text("0.00"),
            nullable=True,
        ),
        sa.Column(
            "sugar_g",
            sa.Numeric(precision=7, scale=2),
            server_default=sa.text("0.00"),
            nullable=True,
        ),
        sa.Column("glycemic_index", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("glycemic_load", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "is_test_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("serving_size_g > 0", name="check_food_serving_size_positive"),
        sa.CheckConstraint("energy_kcal >= 0", name="check_food_energy_kcal_non_negative"),
        sa.CheckConstraint("carbohydrate_g >= 0", name="check_food_carb_non_negative"),
        sa.CheckConstraint("protein_g >= 0", name="check_food_protein_non_negative"),
        sa.CheckConstraint("fat_g >= 0", name="check_food_fat_non_negative"),
        sa.CheckConstraint("fiber_g IS NULL OR fiber_g >= 0", name="check_food_fiber_non_negative"),
        sa.CheckConstraint("sugar_g IS NULL OR sugar_g >= 0", name="check_food_sugar_non_negative"),
        sa.CheckConstraint(
            "glycemic_index IS NULL OR (glycemic_index >= 0 AND glycemic_index <= 150)",
            name="check_food_gi_range",
        ),
        sa.CheckConstraint("glycemic_load IS NULL OR glycemic_load >= 0", name="check_food_gl_non_negative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_foods_name"), "foods", ["name"], unique=False)
    op.create_index(op.f("ix_foods_category"), "foods", ["category"], unique=False)

    # 2. Create 'meal_recommendations' table
    op.create_table(
        "meal_recommendations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_type", sa.String(length=50), nullable=False),
        sa.Column(
            "algorithm_version",
            sa.String(length=50),
            server_default=sa.text("'v1.0-rule_scoring'"),
            nullable=False,
        ),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendation_result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_meal_recommendations_user_id"),
        "meal_recommendations",
        ["user_id"],
        unique=False,
    )

    # 3. Create 'meal_recommendation_items' table
    op.create_table(
        "meal_recommendation_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "serving_multiplier",
            sa.Numeric(precision=4, scale=2),
            server_default=sa.text("1.00"),
            nullable=False,
        ),
        sa.Column("calculated_energy_kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("calculated_carbohydrate_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("calculated_protein_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("calculated_fat_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("calculated_fiber_g", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["meal_recommendations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_meal_recommendation_items_recommendation_id"),
        "meal_recommendation_items",
        ["recommendation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_meal_recommendation_items_food_id"),
        "meal_recommendation_items",
        ["food_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_meal_recommendation_items_food_id"),
        table_name="meal_recommendation_items",
    )
    op.drop_index(
        op.f("ix_meal_recommendation_items_recommendation_id"),
        table_name="meal_recommendation_items",
    )
    op.drop_table("meal_recommendation_items")

    op.drop_index(
        op.f("ix_meal_recommendations_user_id"),
        table_name="meal_recommendations",
    )
    op.drop_table("meal_recommendations")

    op.drop_index(op.f("ix_foods_category"), table_name="foods")
    op.drop_index(op.f("ix_foods_name"), table_name="foods")
    op.drop_table("foods")

