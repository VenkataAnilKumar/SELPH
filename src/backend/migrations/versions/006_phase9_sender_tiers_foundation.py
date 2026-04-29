"""Phase 9 sender tiers foundation

Revision ID: 006_phase9_sender_tiers_foundation
Revises: 005_phase9_twin_briefing_foundation
Create Date: 2026-04-28 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006_phase9_sender_tiers_foundation"
down_revision = "005_phase9_twin_briefing_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sender_tiers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("sender_id", sa.String(length=200), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("tier_label", sa.String(length=100), nullable=True),
        sa.Column("set_by", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_interaction_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sender_id", "platform", name="uq_sender_tiers_user_sender_platform"),
    )
    op.create_index("ix_sender_tiers_user_id", "sender_tiers", ["user_id"])
    op.create_index(
        "ix_sender_tiers_user_platform_tier",
        "sender_tiers",
        ["user_id", "platform", "tier"],
    )


def downgrade() -> None:
    op.drop_index("ix_sender_tiers_user_platform_tier", table_name="sender_tiers")
    op.drop_index("ix_sender_tiers_user_id", table_name="sender_tiers")
    op.drop_table("sender_tiers")
