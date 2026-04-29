"""Phase 10 end-to-end foundation

Revision ID: 008_phase10_end_to_end_foundation
Revises: 007_phase9_batch_pattern_foundation
Create Date: 2026-04-28 21:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "008_phase10_end_to_end_foundation"
down_revision = "007_phase9_batch_pattern_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("twins", sa.Column("twin_operating_mode", sa.String(length=50), nullable=False, server_default="normal"))

    op.add_column("drafts", sa.Column("selph_signature", sa.Text(), nullable=True))
    op.add_column("drafts", sa.Column("selph_twin_id", sa.String(), nullable=True))
    op.add_column("drafts", sa.Column("force_review", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "proactive_suggestions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("suggestion_type", sa.String(length=50), nullable=False),
        sa.Column("contact_id", sa.String(length=200), nullable=True),
        sa.Column("signal_summary", sa.Text(), nullable=False),
        sa.Column("draft_message", sa.Text(), nullable=False),
        sa.Column("urgency_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("value_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("snoozed_until", sa.DateTime(), nullable=True),
        sa.Column("acted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proactive_suggestions_user_id", "proactive_suggestions", ["user_id"])
    op.create_index("ix_proactive_suggestions_user_status", "proactive_suggestions", ["user_id", "status"])

    op.create_table(
        "proactive_preferences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled_types", sa.JSON(), nullable=False),
        sa.Column("cold_threshold_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("open_thread_hours", sa.Integer(), nullable=False, server_default="48"),
        sa.Column("max_suggestions_per_day", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_proactive_preferences_user_id", "proactive_preferences", ["user_id"])

    op.create_table(
        "surge_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("baseline_rate", sa.Float(), nullable=True),
        sa.Column("peak_rate", sa.Float(), nullable=True),
        sa.Column("mode_activated", sa.String(length=50), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_surge_events_user_id", "surge_events", ["user_id"])
    op.create_index("ix_surge_events_user_resolved", "surge_events", ["user_id", "resolved_at"])

    op.create_table(
        "crisis_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("template_type", sa.String(length=50), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crisis_templates_user_id", "crisis_templates", ["user_id"])

    op.create_table(
        "identity_variants",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("profile_name", sa.String(length=100), nullable=False),
        sa.Column("profile_type", sa.String(length=50), nullable=False, server_default="personal_brand"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("vocabulary_description", sa.Text(), nullable=True),
        sa.Column("communication_style", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_variants_user_id", "identity_variants", ["user_id"])
    op.create_index("ix_identity_variants_user_active", "identity_variants", ["user_id", "is_active"])

    op.create_table(
        "channel_profile_mappings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("platform_account", sa.String(length=200), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["identity_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "channel", "platform_account", name="uq_channel_profile_mapping"),
    )
    op.create_index("ix_channel_profile_mappings_user_id", "channel_profile_mappings", ["user_id"])
    op.create_index("ix_channel_profile_mappings_profile_id", "channel_profile_mappings", ["profile_id"])
    op.create_index("ix_channel_profile_mappings_user_channel", "channel_profile_mappings", ["user_id", "channel"])

    op.create_table(
        "style_checkpoints",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("divergence_score", sa.Float(), nullable=False),
        sa.Column("delta_report", sa.JSON(), nullable=False),
        sa.Column("sample_old", sa.Text(), nullable=False),
        sa.Column("sample_new", sa.Text(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("updated_dimensions", sa.JSON(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["identity_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_style_checkpoints_user_id", "style_checkpoints", ["user_id"])
    op.create_index("ix_style_checkpoints_user_decision", "style_checkpoints", ["user_id", "decision"])

    op.create_table(
        "twin_certificates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("twin_public_id", sa.String(length=50), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("private_key_ref", sa.String(length=200), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoke_reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("twin_public_id"),
    )
    op.create_index("ix_twin_certificates_user_id", "twin_certificates", ["user_id"])
    op.create_index("ix_twin_certificates_twin_public_id", "twin_certificates", ["twin_public_id"])

    op.create_table(
        "verification_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("certificate_id", sa.String(), nullable=True),
        sa.Column("twin_public_id", sa.String(length=50), nullable=False),
        sa.Column("message_hash", sa.String(length=200), nullable=False),
        sa.Column("valid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason", sa.String(length=100), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["certificate_id"], ["twin_certificates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_logs_certificate_id", "verification_logs", ["certificate_id"])
    op.create_index("ix_verification_logs_twin_public_id", "verification_logs", ["twin_public_id"])
    op.create_index("ix_verification_logs_twin_verified", "verification_logs", ["twin_public_id", "verified_at"])

    op.create_table(
        "user_privacy_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("processing_mode", sa.String(length=20), nullable=False, server_default="cloud"),
        sa.Column("on_device_capable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("voice_clone_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("avatar_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("cloud_sync_scope", sa.String(length=50), nullable=False, server_default="full"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_privacy_settings_user_id", "user_privacy_settings", ["user_id"])

    op.create_table(
        "t2t_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("initiating_twin", sa.String(length=50), nullable=False),
        sa.Column("receiving_twin", sa.String(length=50), nullable=False),
        sa.Column("session_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="handshake"),
        sa.Column("negotiation_log", sa.JSON(), nullable=False),
        sa.Column("proposal", sa.JSON(), nullable=True),
        sa.Column("initiator_approved", sa.Boolean(), nullable=True),
        sa.Column("receiver_approved", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_t2t_sessions_status", "t2t_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_t2t_sessions_status", table_name="t2t_sessions")
    op.drop_table("t2t_sessions")

    op.drop_index("ix_user_privacy_settings_user_id", table_name="user_privacy_settings")
    op.drop_table("user_privacy_settings")

    op.drop_index("ix_verification_logs_twin_verified", table_name="verification_logs")
    op.drop_index("ix_verification_logs_twin_public_id", table_name="verification_logs")
    op.drop_index("ix_verification_logs_certificate_id", table_name="verification_logs")
    op.drop_table("verification_logs")

    op.drop_index("ix_twin_certificates_twin_public_id", table_name="twin_certificates")
    op.drop_index("ix_twin_certificates_user_id", table_name="twin_certificates")
    op.drop_table("twin_certificates")

    op.drop_index("ix_style_checkpoints_user_decision", table_name="style_checkpoints")
    op.drop_index("ix_style_checkpoints_user_id", table_name="style_checkpoints")
    op.drop_table("style_checkpoints")

    op.drop_index("ix_channel_profile_mappings_user_channel", table_name="channel_profile_mappings")
    op.drop_index("ix_channel_profile_mappings_profile_id", table_name="channel_profile_mappings")
    op.drop_index("ix_channel_profile_mappings_user_id", table_name="channel_profile_mappings")
    op.drop_table("channel_profile_mappings")

    op.drop_index("ix_identity_variants_user_active", table_name="identity_variants")
    op.drop_index("ix_identity_variants_user_id", table_name="identity_variants")
    op.drop_table("identity_variants")

    op.drop_index("ix_crisis_templates_user_id", table_name="crisis_templates")
    op.drop_table("crisis_templates")

    op.drop_index("ix_surge_events_user_resolved", table_name="surge_events")
    op.drop_index("ix_surge_events_user_id", table_name="surge_events")
    op.drop_table("surge_events")

    op.drop_index("ix_proactive_preferences_user_id", table_name="proactive_preferences")
    op.drop_table("proactive_preferences")

    op.drop_index("ix_proactive_suggestions_user_status", table_name="proactive_suggestions")
    op.drop_index("ix_proactive_suggestions_user_id", table_name="proactive_suggestions")
    op.drop_table("proactive_suggestions")

    op.drop_column("drafts", "force_review")
    op.drop_column("drafts", "selph_twin_id")
    op.drop_column("drafts", "selph_signature")

    op.drop_column("twins", "twin_operating_mode")
