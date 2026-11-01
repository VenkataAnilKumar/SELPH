"""Add model columns that were never migrated (users.push_token, drafts telemetry)

Revision ID: 009_model_schema_drift_fix
Revises: 008_phase10_end_to_end_foundation
Create Date: 2026-11-01
"""

from alembic import op
import sqlalchemy as sa

revision = "009_model_schema_drift_fix"
down_revision = "008_phase10_end_to_end_foundation"
branch_labels = None
depends_on = None

DRAFT_COLUMNS = [
    ("generation_source", sa.String()),
    ("llm_model", sa.String()),
    ("fallback_reason", sa.String()),
    ("llm_calls", sa.Integer()),
    ("parse_retry_count", sa.Integer()),
    ("llm_latency_ms", sa.Integer()),
    ("pipeline_latency_ms", sa.Integer()),
    ("estimated_input_tokens", sa.Integer()),
    ("estimated_output_tokens", sa.Integer()),
    ("estimated_total_tokens", sa.Integer()),
    ("estimated_cost_usd", sa.Float()),
]


def _existing(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    user_cols = _existing("users")
    if "push_token" not in user_cols:
        op.add_column("users", sa.Column("push_token", sa.String(), nullable=True))

    draft_cols = _existing("drafts")
    for name, type_ in DRAFT_COLUMNS:
        if name not in draft_cols:
            op.add_column("drafts", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    draft_cols = _existing("drafts")
    for name, _ in reversed(DRAFT_COLUMNS):
        if name in draft_cols:
            op.drop_column("drafts", name)
    if "push_token" in _existing("users"):
        op.drop_column("users", "push_token")
