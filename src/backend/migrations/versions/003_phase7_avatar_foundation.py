"""Phase 7 avatar foundation fields

Revision ID: 003_phase7_avatar_foundation
Revises: 002_phase6_voice_foundation
Create Date: 2026-04-28 00:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_phase7_avatar_foundation"
down_revision = "002_phase6_voice_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # identity_profiles
    op.add_column("identity_profiles", sa.Column("avatar_model_id", sa.String(), nullable=True))
    op.add_column("identity_profiles", sa.Column("avatar_provider", sa.String(), nullable=False, server_default="mock"))
    op.add_column("identity_profiles", sa.Column("avatar_sample_url", sa.Text(), nullable=True))

    # drafts
    op.add_column("drafts", sa.Column("avatar_status", sa.String(), nullable=False, server_default="not_requested"))
    op.add_column("drafts", sa.Column("avatar_video_url", sa.Text(), nullable=True))
    op.add_column("drafts", sa.Column("avatar_provider", sa.String(), nullable=True))
    op.add_column("drafts", sa.Column("avatar_model_id", sa.String(), nullable=True))
    op.add_column("drafts", sa.Column("avatar_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("drafts", "avatar_error")
    op.drop_column("drafts", "avatar_model_id")
    op.drop_column("drafts", "avatar_provider")
    op.drop_column("drafts", "avatar_video_url")
    op.drop_column("drafts", "avatar_status")

    op.drop_column("identity_profiles", "avatar_sample_url")
    op.drop_column("identity_profiles", "avatar_provider")
    op.drop_column("identity_profiles", "avatar_model_id")
