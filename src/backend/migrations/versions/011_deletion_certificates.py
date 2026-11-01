"""Add deletion_certificates for the right to erasure

Revision ID: 011_deletion_certificates
Revises: 010_revoked_tokens
Create Date: 2026-11-01
"""

from alembic import op
import sqlalchemy as sa

revision = "011_deletion_certificates"
down_revision = "010_revoked_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deletion_certificates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("subject_hash", sa.String(length=64), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
    )
    op.create_index("ix_deletion_certificates_subject_hash", "deletion_certificates", ["subject_hash"])


def downgrade() -> None:
    op.drop_index("ix_deletion_certificates_subject_hash", table_name="deletion_certificates")
    op.drop_table("deletion_certificates")
