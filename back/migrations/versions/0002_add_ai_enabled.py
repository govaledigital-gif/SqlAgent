"""add ai_enabled flag to companies

Revision ID: 0002_add_ai_enabled
Revises: 0001_inventory_core
Create Date: 2026-05-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_ai_enabled"
down_revision = "0001_inventory_core"
branch_labels = None
depends_on = None


def _has_column(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    cols = [c.get("name") for c in inspector.get_columns(table_name)]
    return column_name in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("companies") and not _has_column(bind, "companies", "ai_enabled"):
        # Add nullable boolean with server default false for safety
        op.add_column("companies", sa.Column("ai_enabled", sa.Boolean(), nullable=True, server_default=sa.text("0")))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("companies") and _has_column(bind, "companies", "ai_enabled"):
        op.drop_column("companies", "ai_enabled")
