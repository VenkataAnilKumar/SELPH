"""Phase 9 batch pattern approval foundation

Revision ID: 007_phase9_batch_pattern_foundation
Revises: 006_phase9_sender_tiers_foundation
Create Date: 2026-04-28 17:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "007_phase9_batch_pattern_foundation"
down_revision = "006_phase9_sender_tiers_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_clusters",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("cluster_label", sa.String(length=200), nullable=False),
        sa.Column("cluster_summary", sa.Text(), nullable=False),
        sa.Column("message_ids", sa.JSON(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("template_draft", sa.Text(), nullable=False),
        sa.Column("template_approved", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_clusters_user_id", "message_clusters", ["user_id"])
    op.create_index("ix_message_clusters_user_status", "message_clusters", ["user_id", "status"])

    op.create_table(
        "batch_sends",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cluster_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=True),
        sa.Column("sender_id", sa.String(length=200), nullable=False),
        sa.Column("personalized_text", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["message_clusters.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batch_sends_cluster_id", "batch_sends", ["cluster_id"])
    op.create_index("ix_batch_sends_message_id", "batch_sends", ["message_id"])
    op.create_index("ix_batch_sends_draft_id", "batch_sends", ["draft_id"])
    op.create_index("ix_batch_sends_cluster_status", "batch_sends", ["cluster_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_batch_sends_cluster_status", table_name="batch_sends")
    op.drop_index("ix_batch_sends_draft_id", table_name="batch_sends")
    op.drop_index("ix_batch_sends_message_id", table_name="batch_sends")
    op.drop_index("ix_batch_sends_cluster_id", table_name="batch_sends")
    op.drop_table("batch_sends")

    op.drop_index("ix_message_clusters_user_status", table_name="message_clusters")
    op.drop_index("ix_message_clusters_user_id", table_name="message_clusters")
    op.drop_table("message_clusters")
