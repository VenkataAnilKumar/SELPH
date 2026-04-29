"""Phase 9 twin briefing foundation

Revision ID: 005_phase9_twin_briefing_foundation
Revises: 004_phase8_referral_foundation
Create Date: 2026-04-28 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005_phase9_twin_briefing_foundation"
down_revision = "004_phase8_referral_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "twin_briefings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("briefing_type", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cleared_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_twin_briefings_user_id", "twin_briefings", ["user_id"])
    op.create_index(
        "ix_twin_briefings_user_active_priority",
        "twin_briefings",
        ["user_id", "is_active", "priority"],
    )


def downgrade() -> None:
    op.drop_index("ix_twin_briefings_user_active_priority", table_name="twin_briefings")
    op.drop_index("ix_twin_briefings_user_id", table_name="twin_briefings")
    op.drop_table("twin_briefings")
