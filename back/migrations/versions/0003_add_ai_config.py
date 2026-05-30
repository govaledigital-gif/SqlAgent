"""add ai_api_key and ai_quota_per_hour to companies

Revision ID: 0003_add_ai_config
Revises: 0002_add_ai_enabled
Create Date: 2026-05-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_ai_config"
down_revision = "0002_add_ai_enabled"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("companies"):
        cols = [c.get("name") for c in inspector.get_columns("companies")]
        if "ai_api_key" not in cols:
            op.add_column("companies", sa.Column("ai_api_key", sa.String(length=255), nullable=True))
        if "ai_quota_per_hour" not in cols:
            op.add_column("companies", sa.Column("ai_quota_per_hour", sa.String(length=32), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("companies"):
        cols = [c.get("name") for c in inspector.get_columns("companies")]
        if "ai_quota_per_hour" in cols:
            op.drop_column("companies", "ai_quota_per_hour")
        if "ai_api_key" in cols:
            op.drop_column("companies", "ai_api_key")
