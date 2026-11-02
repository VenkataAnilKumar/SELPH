"""Add revoked_tokens table for server-side logout

Revision ID: 010_revoked_tokens
Revises: 009_model_schema_drift_fix
Create Date: 2026-11-01
"""

from alembic import op
import sqlalchemy as sa

revision = "010_revoked_tokens"
down_revision = "009_model_schema_drift_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("token_key", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_type", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_revoked_tokens_token_key", "revoked_tokens", ["token_key"], unique=True)
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_expires_at", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_user_id", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_token_key", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
