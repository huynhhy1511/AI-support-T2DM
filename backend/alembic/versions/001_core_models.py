"""create core user health profile glucose models

Revision ID: 001_core_models
Revises:
Create Date: 2026-10-03 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_core_models"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'users' table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Create 'health_profiles' table (1:1 with users)
    op.create_table(
        "health_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(length=50), nullable=True),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "diabetes_type",
            sa.String(length=50),
            server_default=sa.text("'type2'"),
            nullable=False,
        ),
        sa.Column("diagnosis_year", sa.Integer(), nullable=True),
        sa.Column("activity_level", sa.String(length=100), nullable=True),
        sa.Column("dietary_preference", sa.String(length=100), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # 3. Create 'glucose_records' table (1:N with users)
    op.create_table(
        "glucose_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("glucose_value", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column(
            "unit",
            sa.String(length=20),
            server_default=sa.text("'mmol/L'"),
            nullable=False,
        ),
        sa.Column("measurement_context", sa.String(length=50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "glucose_value > 0",
            name="check_glucose_value_positive",
        ),
        sa.CheckConstraint(
            "unit IN ('mmol/L', 'mg/dL')",
            name="check_glucose_unit_valid",
        ),
        sa.CheckConstraint(
            "measurement_context IS NULL OR measurement_context IN ('fasting', 'before_meal', 'after_meal', 'random', 'other')",
            name="check_glucose_measurement_context_valid",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_glucose_records_user_id"),
        "glucose_records",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index(
        op.f("ix_glucose_records_user_id"),
        table_name="glucose_records",
    )
    op.drop_table("glucose_records")
    op.drop_table("health_profiles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
