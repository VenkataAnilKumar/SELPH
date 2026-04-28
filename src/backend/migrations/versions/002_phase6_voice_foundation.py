"""Phase 6 voice foundation fields

Revision ID: 002_phase6_voice_foundation
Revises: 001_initial_schema
Create Date: 2026-04-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_phase6_voice_foundation"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # identity_profiles
    op.add_column("identity_profiles", sa.Column("voice_model_id", sa.String(), nullable=True))
    op.add_column("identity_profiles", sa.Column("voice_provider", sa.String(), nullable=False, server_default="mock"))
    op.add_column("identity_profiles", sa.Column("voice_sample_url", sa.Text(), nullable=True))

    # drafts
    op.add_column("drafts", sa.Column("voice_status", sa.String(), nullable=False, server_default="not_requested"))
    op.add_column("drafts", sa.Column("voice_audio_url", sa.Text(), nullable=True))
    op.add_column("drafts", sa.Column("voice_provider", sa.String(), nullable=True))
    op.add_column("drafts", sa.Column("voice_model_id", sa.String(), nullable=True))
    op.add_column("drafts", sa.Column("voice_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("drafts", "voice_error")
    op.drop_column("drafts", "voice_model_id")
    op.drop_column("drafts", "voice_provider")
    op.drop_column("drafts", "voice_audio_url")
    op.drop_column("drafts", "voice_status")

    op.drop_column("identity_profiles", "voice_sample_url")
    op.drop_column("identity_profiles", "voice_provider")
    op.drop_column("identity_profiles", "voice_model_id")
