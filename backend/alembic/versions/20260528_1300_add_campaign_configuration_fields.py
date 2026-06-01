"""Add campaign configuration fields.

Revision ID: 20260528_1300
Revises: 20260528_1200
Create Date: 2026-05-28 13:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260528_1300"
down_revision: str | None = "20260528_1200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("campaigns", "description"):
        op.add_column("campaigns", sa.Column("description", sa.Text(), nullable=True))
    if not _has_column("campaigns", "reward_coins"):
        op.add_column("campaigns", sa.Column("reward_coins", sa.Integer(), nullable=False, server_default="0"))
        op.alter_column("campaigns", "reward_coins", server_default=None)
    if not _has_column("campaigns", "tasks"):
        op.add_column("campaigns", sa.Column("tasks", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")))
        op.alter_column("campaigns", "tasks", server_default=None)


def downgrade() -> None:
    if _has_column("campaigns", "tasks"):
        op.drop_column("campaigns", "tasks")
    if _has_column("campaigns", "reward_coins"):
        op.drop_column("campaigns", "reward_coins")
    if _has_column("campaigns", "description"):
        op.drop_column("campaigns", "description")
