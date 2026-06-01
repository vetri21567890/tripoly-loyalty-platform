"""Add loyalty program settings and tier status.

Revision ID: 20260528_1200
Revises: 20260527_1903
Create Date: 2026-05-28 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260528_1200"
down_revision: Union[str, None] = "20260527_1903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "loyalty_program_settings" not in tables:
        op.create_table(
            "loyalty_program_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("setting_key", sa.String(length=128), nullable=False),
            sa.Column("setting_value", sa.Text(), nullable=False),
            sa.Column("value_type", sa.String(length=32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("setting_key"),
        )
        op.create_index(op.f("ix_loyalty_program_settings_setting_key"), "loyalty_program_settings", ["setting_key"], unique=False)
    tier_columns = {column["name"] for column in inspector.get_columns("loyalty_tiers")}
    if "status" not in tier_columns:
        op.add_column("loyalty_tiers", sa.Column("status", sa.String(length=32), server_default="active", nullable=False))


def downgrade() -> None:
    op.drop_column("loyalty_tiers", "status")
    op.drop_index(op.f("ix_loyalty_program_settings_setting_key"), table_name="loyalty_program_settings")
    op.drop_table("loyalty_program_settings")
