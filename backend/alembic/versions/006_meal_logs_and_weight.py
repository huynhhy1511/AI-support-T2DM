"""create meal_logs, meal_log_items, and weight_records tables

Revision ID: 006_meal_logs_and_weight
Revises: 005_health_profile_clinical
Create Date: 2026-11-27 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "006_meal_logs_and_weight"
down_revision: Union[str, None] = "005_health_profile_clinical"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. meal_logs
    op.create_table(
        "meal_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meal_recommendations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("meal_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meal_logs_meal_type",
        ),
        sa.CheckConstraint(
            "status IN ('eaten', 'partially_eaten', 'skipped', 'eaten_other')",
            name="ck_meal_logs_status",
        ),
    )
    op.create_index("ix_meal_logs_user_id", "meal_logs", ["user_id"])
    op.create_index("ix_meal_logs_recommendation_id", "meal_logs", ["recommendation_id"])
    op.create_index("ix_meal_logs_meal_date", "meal_logs", ["meal_date"])

    # 2. meal_log_items
    op.create_table(
        "meal_log_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "meal_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meal_logs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "food_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("foods.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("custom_food_name", sa.String(length=200), nullable=True),
        sa.Column("serving_g", sa.Float(), nullable=False),
        sa.Column("calories_kcal", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("sodium_mg", sa.Float(), nullable=True),
        sa.CheckConstraint("serving_g > 0", name="ck_meal_log_items_serving_positive"),
        sa.CheckConstraint("calories_kcal >= 0", name="ck_meal_log_items_calories_non_negative"),
        sa.CheckConstraint("carbs_g >= 0", name="ck_meal_log_items_carbs_non_negative"),
        sa.CheckConstraint("protein_g >= 0", name="ck_meal_log_items_protein_non_negative"),
        sa.CheckConstraint("fat_g >= 0", name="ck_meal_log_items_fat_non_negative"),
        sa.CheckConstraint(
            "fiber_g IS NULL OR fiber_g >= 0",
            name="ck_meal_log_items_fiber_non_negative",
        ),
        sa.CheckConstraint(
            "sodium_mg IS NULL OR sodium_mg >= 0",
            name="ck_meal_log_items_sodium_non_negative",
        ),
    )
    op.create_index("ix_meal_log_items_meal_log_id", "meal_log_items", ["meal_log_id"])
    op.create_index("ix_meal_log_items_food_id", "meal_log_items", ["food_id"])

    # 3. weight_records
    op.create_table(
        "weight_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("weight_kg > 0", name="ck_weight_records_weight_positive"),
        sa.UniqueConstraint("user_id", "recorded_at", name="uq_weight_records_user_date"),
    )
    op.create_index("ix_weight_records_user_id", "weight_records", ["user_id"])
    op.create_index("ix_weight_records_recorded_at", "weight_records", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_weight_records_recorded_at", table_name="weight_records")
    op.drop_index("ix_weight_records_user_id", table_name="weight_records")
    op.drop_table("weight_records")

    op.drop_index("ix_meal_log_items_food_id", table_name="meal_log_items")
    op.drop_index("ix_meal_log_items_meal_log_id", table_name="meal_log_items")
    op.drop_table("meal_log_items")

    op.drop_index("ix_meal_logs_meal_date", table_name="meal_logs")
    op.drop_index("ix_meal_logs_recommendation_id", table_name="meal_logs")
    op.drop_index("ix_meal_logs_user_id", table_name="meal_logs")
    op.drop_table("meal_logs")
