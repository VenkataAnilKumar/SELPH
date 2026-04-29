"""Initial schema with 9 tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-04-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Required for Vector(...) columns used in identity_profiles/topics.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Alembic creates alembic_version with VARCHAR(32) by default; our revision
    # IDs are longer, so widen the column before any upgrade writes to it.
    op.execute(
        "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(256)"
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create twins table
    op.create_table(
        'twins',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False, server_default='professional'),
        sa.Column('tone', sa.String(), nullable=False, server_default='friendly'),
        sa.Column('vocab', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('avg_response_length', sa.Integer(), nullable=False, server_default='150'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_twins_user_id', 'twins', ['user_id'])

    # Create identity_profiles table
    op.create_table(
        'identity_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('vocabulary_description', sa.Text(), nullable=True),
        sa.Column('communication_style', sa.Text(), nullable=True),
        sa.Column('topics_known_embedding', Vector(1536), nullable=True),
        sa.Column('topics_avoided_embedding', Vector(1536), nullable=True),
        sa.Column('embedding_model', sa.String(), nullable=False, server_default='text-embedding-3-small'),
        sa.Column('topics_known_text', sa.Text(), nullable=True),
        sa.Column('topics_avoided_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_identity_profiles_user_id', 'identity_profiles', ['user_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=False),
        sa.Column('sender_name', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='received'),
        sa.Column('channel_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_user_id_channel', 'messages', ['user_id', 'channel'])
    op.create_index('ix_messages_status', 'messages', ['status'])

    # Create drafts table
    op.create_table(
        'drafts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('twin_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('edited_content', sa.Text(), nullable=True),
        sa.Column('sent_response', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('confidence_label', sa.String(), nullable=False, server_default='Medium'),
        sa.Column('confidence_reasoning', sa.Text(), nullable=True),
        sa.Column('moderation_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('moderation_flags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending_approval'),
        sa.Column('user_action', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['twin_id'], ['twins.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id'),
    )
    op.create_index('ix_drafts_user_id_status', 'drafts', ['user_id', 'status'])
    op.create_index('ix_drafts_twin_id', 'drafts', ['twin_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Create topics table
    op.create_table(
        'topics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('topic_type', sa.String(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_topics_user_id_type', 'topics', ['user_id', 'topic_type'])

    # Create consents table
    op.create_table(
        'consents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_consents_user_id_type', 'consents', ['user_id', 'consent_type'])

    # Create channel_credentials table
    op.create_table(
        'channel_credentials',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('credential_type', sa.String(), nullable=False, server_default='oauth_token'),
        sa.Column('credential_value', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_channel_credentials_user_channel', 'channel_credentials', ['user_id', 'channel'])


def downgrade() -> None:
    op.drop_index('ix_channel_credentials_user_channel', table_name='channel_credentials')
    op.drop_table('channel_credentials')
    
    op.drop_index('ix_consents_user_id_type', table_name='consents')
    op.drop_table('consents')
    
    op.drop_index('ix_topics_user_id_type', table_name='topics')
    op.drop_table('topics')
    
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_drafts_twin_id', table_name='drafts')
    op.drop_index('ix_drafts_user_id_status', table_name='drafts')
    op.drop_table('drafts')
    
    op.drop_index('ix_messages_status', table_name='messages')
    op.drop_index('ix_messages_user_id_channel', table_name='messages')
    op.drop_table('messages')
    
    op.drop_index('ix_identity_profiles_user_id', table_name='identity_profiles')
    op.drop_table('identity_profiles')
    
    op.drop_index('ix_twins_user_id', table_name='twins')
    op.drop_table('twins')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
