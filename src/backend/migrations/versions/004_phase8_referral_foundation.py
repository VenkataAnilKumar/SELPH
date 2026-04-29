"""Phase 8 referral foundation

Revision ID: 004_phase8_referral_foundation
Revises: 003_phase7_avatar_foundation
Create Date: 2026-04-28 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004_phase8_referral_foundation"
down_revision = "003_phase7_avatar_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referral_invites",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("referrer_user_id", sa.String(), nullable=False),
        sa.Column("invitee_user_id", sa.String(), nullable=True),
        sa.Column("invitee_email", sa.String(), nullable=False),
        sa.Column("referral_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("reward_status", sa.String(), nullable=False, server_default="unclaimed"),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["referrer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["invitee_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_referral_invites_referrer_user_id", "referral_invites", ["referrer_user_id"])
    op.create_index("ix_referral_invites_invitee_user_id", "referral_invites", ["invitee_user_id"])
    op.create_index("ix_referral_invites_invitee_email", "referral_invites", ["invitee_email"])
    op.create_index("ix_referral_invites_referral_code", "referral_invites", ["referral_code"])
    op.create_index("ix_referral_invites_referrer_status", "referral_invites", ["referrer_user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_referral_invites_referrer_status", table_name="referral_invites")
    op.drop_index("ix_referral_invites_referral_code", table_name="referral_invites")
    op.drop_index("ix_referral_invites_invitee_email", table_name="referral_invites")
    op.drop_index("ix_referral_invites_invitee_user_id", table_name="referral_invites")
    op.drop_index("ix_referral_invites_referrer_user_id", table_name="referral_invites")
    op.drop_table("referral_invites")
