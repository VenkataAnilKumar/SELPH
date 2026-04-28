# SELPH — Database Schema

> Version: 1.0
> Created: 2026-04-24
> Folder: 05-technical
> Status: Draft — Source of truth before writing any migration

---

## Overview

This document is the canonical PostgreSQL schema for SELPH. Every table, index, constraint, and relationship is defined here. Migrations are generated from this schema — never the other way around.

Database: PostgreSQL 16 (Railway managed PostgreSQL)

---

## Schema: `selph`

All tables live in the `selph` schema. Set search path:

```sql
CREATE SCHEMA IF NOT EXISTS selph;
SET search_path = selph;

-- pgvector extension for on-DB similarity search (no external vector store needed)
CREATE EXTENSION IF NOT EXISTS vector;
```

> **Storage Architecture Note:**
> - All vector queries (similar past responses, style vectors, topic vectors) use **pgvector** — co-located on Railway PostgreSQL, no network hop, <5ms.
> - Audit logs use the `audit_logs` PostgreSQL table — partition by month at scale.
> - LangGraph interrupted state uses **PostgresSaver** for MVP. Switch to RedisSaver at higher concurrency.
>
> Full architecture: [SELPH_System-Architecture.md](../05-technical/SELPH_System-Architecture.md)

---

## Table: `users`

Core account table. Authentication data only — no identity or profile data here.

```sql
CREATE TABLE users (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email             VARCHAR(255) NOT NULL UNIQUE,
  phone             VARCHAR(20),
  full_name         VARCHAR(200) NOT NULL,
  password_hash     VARCHAR(255),             -- null if social-only login
  auth_provider     VARCHAR(50) DEFAULT 'email',  -- "email" | "google" | "apple"
  auth_provider_id  VARCHAR(255),             -- provider's user ID
  is_verified       BOOLEAN     NOT NULL DEFAULT false,
  is_active         BOOLEAN     NOT NULL DEFAULT true,
  is_suspended      BOOLEAN     NOT NULL DEFAULT false,
  suspension_reason TEXT,
  last_login_at     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth_provider ON users(auth_provider, auth_provider_id);
```

---

## Table: `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  VARCHAR(255) NOT NULL UNIQUE,    -- SHA-256 of token
  expires_at  TIMESTAMPTZ NOT NULL,
  revoked_at  TIMESTAMPTZ,
  ip_address  INET        NOT NULL,
  user_agent  TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
```

---

## Table: `user_consents`

Immutable audit trail of every consent action.

```sql
CREATE TABLE user_consents (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  consent_type   VARCHAR(100) NOT NULL CHECK (consent_type IN (
                   'terms_of_service', 'privacy_policy', 'digital_twin_agreement',
                   'identity_verification', 'voice_clone', 'avatar_clone',
                   'instagram_ingestion', 'gmail_ingestion', 'twitter_ingestion',
                   'transparent_mode', 'private_mode'
                 )),
  version        VARCHAR(20) NOT NULL,          -- document version e.g. "1.0"
  granted        BOOLEAN     NOT NULL,
  granted_at     TIMESTAMPTZ,
  revoked_at     TIMESTAMPTZ,
  ip_address     INET        NOT NULL,
  user_agent     TEXT        NOT NULL,
  geo_country    CHAR(2),                       -- ISO 3166-1 alpha-2
  signature_text TEXT,                          -- what the user acknowledged
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_consents_user_type ON user_consents(user_id, consent_type);
CREATE INDEX idx_consents_granted ON user_consents(user_id, granted, consent_type);
```

---

## Table: `identity_profiles`

The core twin profile. One row per user.

```sql
CREATE TABLE identity_profiles (
  id                  UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  -- Multi-identity: one user can have multiple profiles (Creator, Professional, Business)
  -- UNIQUE(user_id) removed to support multi-identity — use is_primary flag instead
  profile_name        VARCHAR(100) NOT NULL DEFAULT 'Default',
  profile_type        VARCHAR(50)  NOT NULL DEFAULT 'personal_brand',
                        -- personal_brand | professional | business | private
  is_primary          BOOLEAN  NOT NULL DEFAULT false,
  is_active           BOOLEAN  NOT NULL DEFAULT true,
  version             INTEGER  NOT NULL DEFAULT 1,

  -- Name (used by Twin Engine prompt builder)
  first_name          VARCHAR(100) NOT NULL,
  last_name           VARCHAR(100) NOT NULL,

  -- Domain & Role
  domain              VARCHAR(100) NOT NULL,
  sub_domain          VARCHAR(100),
  professional_title  VARCHAR(100),

  -- Communication Style
  tone                VARCHAR(200) NOT NULL,
  formality_level     SMALLINT NOT NULL DEFAULT 3
                        CHECK (formality_level BETWEEN 1 AND 5),
  avg_response_length SMALLINT NOT NULL DEFAULT 80,
  response_length_min SMALLINT NOT NULL DEFAULT 20,
  response_length_max SMALLINT NOT NULL DEFAULT 200,
  emoji_usage         DECIMAL(3,2) NOT NULL DEFAULT 0.30
                        CHECK (emoji_usage BETWEEN 0.0 AND 1.0),
  punctuation_style   VARCHAR(50) DEFAULT 'standard',

  -- Personality
  greeting_style      VARCHAR(100),
  sign_off_style      VARCHAR(100),
  personality_words   TEXT[]   NOT NULL DEFAULT '{}',
  bio_summary         TEXT,

  -- Calibration counters
  total_drafts        INTEGER  NOT NULL DEFAULT 0,
  total_approved      INTEGER  NOT NULL DEFAULT 0,
  total_edited        INTEGER  NOT NULL DEFAULT 0,
  total_rejected      INTEGER  NOT NULL DEFAULT 0,
  approval_rate       DECIMAL(4,3) NOT NULL DEFAULT 0.0,
  trust_stage         SMALLINT NOT NULL DEFAULT 1
                        CHECK (trust_stage IN (1, 2, 3)),
  stage_advanced_at   TIMESTAMPTZ,
  calibration_due_at  TIMESTAMPTZ,

  -- Status
  is_active           BOOLEAN  NOT NULL DEFAULT true,
  activated_at        TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Table: `identity_profile_snapshots`

Version history of the identity profile (for rollback + audit).

```sql
CREATE TABLE identity_profile_snapshots (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID        NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  version     INTEGER     NOT NULL,
  snapshot    JSONB       NOT NULL,
  reason      VARCHAR(100),   -- "weekly_calibration" | "bulk_edit" | "auto_update" | "user_edit"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, version)
);

CREATE INDEX idx_snapshots_profile ON identity_profile_snapshots(profile_id, version DESC);
```

---

## Table: `identity_vocabulary`

Top words/phrases that define the user's writing fingerprint.

```sql
CREATE TABLE identity_vocabulary (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID        NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  word        VARCHAR(100) NOT NULL,
  frequency   INTEGER     NOT NULL DEFAULT 1,
  weight      DECIMAL(4,3) NOT NULL DEFAULT 0.500
                CHECK (weight BETWEEN 0.0 AND 1.0),
  source      VARCHAR(50) NOT NULL,   -- "instagram" | "gmail" | "twitter" | "manual"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, word)
);

CREATE INDEX idx_vocabulary_profile ON identity_vocabulary(profile_id);
CREATE INDEX idx_vocabulary_weight ON identity_vocabulary(profile_id, weight DESC);
```

---

## Table: `identity_topics`

Topics the user knows, avoids, or is expert in.

```sql
CREATE TABLE identity_topics (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID        NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  topic       VARCHAR(200) NOT NULL,
  type        VARCHAR(20) NOT NULL CHECK (type IN ('known', 'avoided', 'expert')),
  confidence  DECIMAL(3,2) NOT NULL DEFAULT 0.80
                CHECK (confidence BETWEEN 0.0 AND 1.0),
  source      VARCHAR(50),   -- "user_stated" | "inferred" | "content_analysis"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, topic)
);

CREATE INDEX idx_topics_profile ON identity_topics(profile_id, type);
```

---

## Table: `identity_samples`

Real response examples used for few-shot prompting.

```sql
CREATE TABLE identity_samples (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id    UUID        NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  channel       VARCHAR(50) NOT NULL,
  incoming      TEXT        NOT NULL,
  response      TEXT        NOT NULL,
  source        VARCHAR(20) NOT NULL,   -- "ingested" | "approved_draft" | "manual"
  quality_score DECIMAL(3,2)
                  CHECK (quality_score IS NULL OR quality_score BETWEEN 0.0 AND 1.0),
  vector_id     VARCHAR(200),           -- reserved for future external vector store reference
  is_active     BOOLEAN     NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_samples_profile_channel ON identity_samples(profile_id, channel);
CREATE INDEX idx_samples_quality ON identity_samples(profile_id, quality_score DESC NULLS LAST);
```

---

## Table: `identity_channel_profiles`

Per-channel style overrides for the twin.

```sql
CREATE TABLE identity_channel_profiles (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      UUID        NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  channel         VARCHAR(50) NOT NULL,
  tone_override   VARCHAR(200),
  max_length      SMALLINT,
  emoji_override  DECIMAL(3,2)
                    CHECK (emoji_override IS NULL OR emoji_override BETWEEN 0.0 AND 1.0),
  format_hint     VARCHAR(100),
  is_active       BOOLEAN     NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, channel)
);
```

---

## Table: `channel_connections`

OAuth tokens for each connected channel per user.

```sql
CREATE TABLE channel_connections (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel           VARCHAR(50) NOT NULL,   -- "instagram_dm" | "gmail" | "twitter_dm"
  platform_user_id  VARCHAR(200),           -- platform's user/account ID
  access_token      TEXT        NOT NULL,   -- encrypted at application level
  refresh_token     TEXT,                   -- encrypted at application level
  token_expires_at  TIMESTAMPTZ,
  scopes            TEXT[],                 -- granted OAuth scopes
  webhook_id        VARCHAR(200),           -- platform's webhook subscription ID
  is_active         BOOLEAN     NOT NULL DEFAULT true,
  last_sync_at      TIMESTAMPTZ,
  ingestion_status  VARCHAR(20) NOT NULL DEFAULT 'pending'
                      CHECK (ingestion_status IN ('pending', 'in_progress', 'complete', 'failed')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, channel)
);

CREATE INDEX idx_connections_user ON channel_connections(user_id, is_active);
```

---

## Table: `pending_drafts`

Drafts waiting for human approval. This is LangGraph's interrupt storage.

```sql
CREATE TABLE pending_drafts (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  langgraph_thread_id VARCHAR(200) NOT NULL UNIQUE,  -- LangGraph thread for resume
  channel           VARCHAR(50) NOT NULL,
  sender_id         VARCHAR(200) NOT NULL,
  sender_name       VARCHAR(200),
  incoming_message  TEXT        NOT NULL,
  draft_content     TEXT,                    -- null if twin couldn't draft
  confidence_score  DECIMAL(4,3),
  confidence_label  VARCHAR(20) CHECK (confidence_label IN ('ready', 'review', 'needs_input')),
  confidence_factors JSONB,
  moderation_passed BOOLEAN,
  moderation_flags  TEXT[]       DEFAULT '{}',
  status            VARCHAR(20) NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'approved', 'edited', 'rejected', 'skipped', 'expired', 'flagged')),
  final_content     TEXT,                    -- what was actually sent
  human_action      VARCHAR(20) CHECK (human_action IN ('approve', 'edit', 'reject', 'skip')),
  actioned_at       TIMESTAMPTZ,
  expires_at        TIMESTAMPTZ NOT NULL,    -- 24 hours from creation
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_drafts_user_status ON pending_drafts(user_id, status);
CREATE INDEX idx_drafts_expires ON pending_drafts(expires_at) WHERE status = 'pending';
```

---

## Table: `audit_logs`

Immutable log of all actions in the system.

```sql
CREATE TABLE audit_logs (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        REFERENCES users(id) ON DELETE SET NULL,
  action      VARCHAR(100) NOT NULL,
  -- Actions: "draft_generated" | "draft_approved" | "draft_edited" |
  --          "draft_rejected" | "draft_skipped" | "message_sent" |
  --          "consent_granted" | "consent_revoked" | "account_created" |
  --          "account_deleted" | "voice_clone_created" | "avatar_created" |
  --          "channel_connected" | "channel_disconnected" | "data_exported" |
  --          "abuse_report_received" | "account_suspended"
  entity_type VARCHAR(50),              -- "draft" | "consent" | "channel" | "user"
  entity_id   UUID,                     -- ID of the affected entity
  metadata    JSONB,                    -- action-specific data
  ip_address  INET,
  user_agent  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at DESC);
-- Partition by month for large-scale retention management
```

---

## Table: `abuse_reports`

Reports of harmful AI-generated content (India IT Rules 2026 + general abuse).

```sql
CREATE TABLE abuse_reports (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  reported_by     UUID        REFERENCES users(id) ON DELETE SET NULL,
  twin_user_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
  report_type     VARCHAR(50) NOT NULL CHECK (report_type IN (
                    'impersonation', 'harmful_content', 'non_consensual', 'fraud', 'spam'
                  )),
  severity        VARCHAR(20) NOT NULL DEFAULT 'medium'
                    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  content_url     TEXT,
  description     TEXT        NOT NULL,
  evidence_urls   TEXT[],
  status          VARCHAR(20) NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'investigating', 'resolved', 'dismissed')),
  resolved_at     TIMESTAMPTZ,
  resolution_note TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_severity ON abuse_reports(severity, status, created_at);
CREATE INDEX idx_reports_twin ON abuse_reports(twin_user_id, status);
```

---

## Table: `biometric_assets`

Tracks voice and avatar model creation status (actual files in S3/Chatterbox/Linly-Talker or optional premium provider).

```sql
CREATE TABLE biometric_assets (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID        NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

  -- Voice Clone
  voice_raw_s3_key  VARCHAR(500),               -- deleted after clone created
  voice_model_id    VARCHAR(200),               -- Voice provider model ID: Chatterbox (default) or ElevenLabs (optional, encrypted)
  voice_status      VARCHAR(20) NOT NULL DEFAULT 'none'
                      CHECK (voice_status IN ('none', 'recording_uploaded', 'clone_creating', 'clone_ready', 'deleted')),
  voice_created_at  TIMESTAMPTZ,
  voice_raw_delete_scheduled_at TIMESTAMPTZ,   -- 90 days after clone creation

  -- Avatar Clone
  avatar_raw_s3_key VARCHAR(500),               -- deleted after model created
  avatar_model_id   VARCHAR(200),               -- Avatar provider model ID: Linly-Talker (default) or HeyGen (optional, encrypted)
  avatar_status     VARCHAR(20) NOT NULL DEFAULT 'none'
                      CHECK (avatar_status IN ('none', 'video_uploaded', 'avatar_creating', 'avatar_ready', 'deleted')),
  avatar_created_at TIMESTAMPTZ,
  avatar_raw_delete_scheduled_at TIMESTAMPTZ,  -- 90 days after model creation

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for scheduled deletion cleanup job
CREATE INDEX idx_biometric_voice_delete ON biometric_assets(voice_raw_delete_scheduled_at)
  WHERE voice_status = 'clone_ready';
CREATE INDEX idx_biometric_avatar_delete ON biometric_assets(avatar_raw_delete_scheduled_at)
  WHERE avatar_status = 'avatar_ready';
```

---

## Table: `subscriptions`

Billing and plan management.

```sql
CREATE TABLE subscriptions (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID        NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  plan                VARCHAR(20) NOT NULL DEFAULT 'free'
                        CHECK (plan IN ('free', 'creator', 'pro', 'studio', 'enterprise')),
  status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'past_due', 'cancelled', 'paused')),
  stripe_customer_id  VARCHAR(100),
  stripe_subscription_id VARCHAR(100),
  current_period_start TIMESTAMPTZ,
  current_period_end  TIMESTAMPTZ,
  cancel_at           TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Full Entity Relationship Summary

```
users
  ├── refresh_tokens (1:many)
  ├── user_consents (1:many)
  ├── identity_profiles (1:1)
  │     ├── identity_profile_snapshots (1:many)
  │     ├── identity_vocabulary (1:many)
  │     ├── identity_topics (1:many)
  │     ├── identity_samples (1:many)
  │     └── identity_channel_profiles (1:many)
  ├── channel_connections (1:many)
  ├── pending_drafts (1:many)
  ├── audit_logs (1:many)
  ├── abuse_reports (1:many — as reporter or as subject)
  ├── biometric_assets (1:1)
  └── subscriptions (1:1)
```

---

## Migration Strategy

```
Tool: Alembic (async-compatible with SQLAlchemy async)
Naming: YYYYMMDD_NNNN_description.py (e.g., 20260424_0001_initial_schema.py)
Policy: Never edit a migration that has been applied to staging or production
Rollback: Every migration must have a downgrade() function
Order:
  0001 — users, refresh_tokens
  0002 — user_consents
  0003 — identity_profiles, identity_profile_snapshots
  0004 — identity_vocabulary, identity_topics, identity_samples, identity_channel_profiles
  0005 — channel_connections
  0006 — pending_drafts
  0007 — audit_logs
  0008 — abuse_reports, biometric_assets
  0009 — subscriptions

Note: LangGraph's PostgresSaver creates its own tables (checkpoints, checkpoint_blobs,
checkpoint_writes) via PostgresSaver.setup(). Call this once at app startup — do not
manually define or version-control these tables. They are separate from SELPH migrations.
In Phase 2+, LangGraph state moves to Redis (RedisSaver). These tables become unused.
```

---

## Performance Notes

- `pending_drafts` will be high-traffic. Index on `(user_id, status)` is critical.
- `audit_logs` will grow large. Plan to partition by month for MVP. Migrate to a dedicated time-series store at scale.
- `identity_vocabulary` and `identity_samples` should be limited in application layer (top 200 words, top 50 samples per channel) to prevent unbounded growth.
- All `TEXT` columns storing OAuth tokens must be encrypted at the application layer before write (not just at-rest Railway PostgreSQL encryption).
- `identity_profiles` now supports multiple rows per user (multi-identity). Ensure `is_primary = true` for exactly one profile per user via application-level constraint.

---

## Tables: Feature Expansion (Added 2026-04-27)

Migration batch: `0010` — apply after all existing migrations

### Table: `twin_briefings`

Time-scoped context injected into every twin prompt while active.

```sql
CREATE TABLE twin_briefings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  briefing_type   VARCHAR(50) NOT NULL CHECK (briefing_type IN (
                    'fact', 'opinion', 'instruction', 'availability', 'boundary'
                  )),
  topic           VARCHAR(200) NOT NULL,
  content         TEXT NOT NULL,
  priority        SMALLINT NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
  is_active       BOOLEAN NOT NULL DEFAULT true,
  expires_at      TIMESTAMPTZ,
  max_uses        INTEGER,
  use_count       INTEGER NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  cleared_at      TIMESTAMPTZ
);

CREATE INDEX idx_briefings_user_active ON twin_briefings(user_id, is_active)
  WHERE is_active = true;
```

---

### Table: `sender_tiers`

Per-sender routing tier (VIP, Priority, Standard, Cold).

```sql
CREATE TABLE sender_tiers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sender_id       VARCHAR(200) NOT NULL,
  platform        VARCHAR(50) NOT NULL,
  tier            SMALLINT NOT NULL DEFAULT 2 CHECK (tier BETWEEN 0 AND 3),
  tier_label      VARCHAR(100),
  set_by          VARCHAR(20) NOT NULL DEFAULT 'user',
  notes           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, sender_id, platform)
);

CREATE INDEX idx_sender_tiers_lookup ON sender_tiers(user_id, sender_id, platform);
```

---

### Tables: `message_clusters` and `batch_sends`

Batch pattern approval — semantic clustering and personalized sends.

```sql
CREATE TABLE message_clusters (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  cluster_label     VARCHAR(200) NOT NULL,
  cluster_summary   TEXT NOT NULL,
  message_ids       UUID[] NOT NULL,
  message_count     INTEGER NOT NULL,
  template_draft    TEXT NOT NULL,
  template_approved TEXT,
  status            VARCHAR(50) NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','approved','rejected','sent')),
  approved_at       TIMESTAMPTZ,
  sent_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE batch_sends (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id        UUID NOT NULL REFERENCES message_clusters(id) ON DELETE CASCADE,
  message_id        UUID NOT NULL,
  sender_id         VARCHAR(200) NOT NULL,
  personalized_text TEXT NOT NULL,
  sent_at           TIMESTAMPTZ,
  status            VARCHAR(50) NOT NULL DEFAULT 'queued'
);

CREATE INDEX idx_clusters_user_status ON message_clusters(user_id, status);
```

---

### Tables: `proactive_suggestions` and `proactive_preferences`

Proactive twin outbound intelligence.

```sql
CREATE TABLE proactive_suggestions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  suggestion_type   VARCHAR(50) NOT NULL,
  contact_id        VARCHAR(200),
  signal_summary    TEXT NOT NULL,
  draft_message     TEXT NOT NULL,
  urgency_score     DECIMAL(3,2) NOT NULL,
  value_score       DECIMAL(3,2) NOT NULL,
  status            VARCHAR(50) NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','approved','dismissed','sent','never')),
  snoozed_until     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  acted_at          TIMESTAMPTZ
);

CREATE TABLE proactive_preferences (
  user_id               UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  enabled               BOOLEAN NOT NULL DEFAULT true,
  enabled_types         VARCHAR(50)[] NOT NULL DEFAULT ARRAY['cold_relationship','deal_signal','open_thread'],
  cold_threshold_days   INTEGER NOT NULL DEFAULT 14,
  open_thread_hours     INTEGER NOT NULL DEFAULT 48,
  max_suggestions_per_day INTEGER NOT NULL DEFAULT 5
);
```

---

### Tables: `surge_events` and `crisis_templates`

Crisis and surge mode.

```sql
CREATE TABLE surge_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  trigger_type    VARCHAR(50) NOT NULL,
  trigger_value   DECIMAL(8,2),
  threshold_value DECIMAL(8,2),
  baseline_rate   DECIMAL(8,2),
  peak_rate       DECIMAL(8,2),
  mode_activated  VARCHAR(50) NOT NULL,
  activated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at     TIMESTAMPTZ,
  resolution_type VARCHAR(50)
);

CREATE TABLE crisis_templates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  label           VARCHAR(100) NOT NULL,
  content         TEXT NOT NULL,
  template_type   VARCHAR(50) NOT NULL DEFAULT 'custom',
  approved_at     TIMESTAMPTZ NOT NULL,
  last_used_at    TIMESTAMPTZ
);
```

---

### Tables: `twin_certificates` and `verification_log`

Twin Verification Public API.

```sql
CREATE TABLE twin_certificates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  twin_id         VARCHAR(50) UNIQUE NOT NULL,  -- public twin ID: twn_xxxxx
  public_key      TEXT NOT NULL,
  private_key_ref VARCHAR(200) NOT NULL,         -- encrypted key reference (libsodium), never stored raw
  issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL,
  revoked_at      TIMESTAMPTZ,
  revoke_reason   VARCHAR(200)
);

CREATE TABLE verification_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  twin_id         VARCHAR(50) NOT NULL,
  message_hash    VARCHAR(200) NOT NULL,
  result          VARCHAR(20) NOT NULL CHECK (result IN ('valid','invalid','revoked')),
  requester_ip    INET,
  requested_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_verification_log_twin ON verification_log(twin_id, requested_at DESC);
```

---

### Table: `channel_profile_mappings`

Channel-to-identity-profile routing for multi-identity.

```sql
CREATE TABLE channel_profile_mappings (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id       UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  channel          VARCHAR(50) NOT NULL,
  platform_account VARCHAR(200),
  priority         SMALLINT NOT NULL DEFAULT 1,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, channel, platform_account)
);
```

---

### Table: `style_checkpoints`

Style evolution and intentional identity refresh.

```sql
CREATE TABLE style_checkpoints (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id          UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  trigger_type        VARCHAR(50) NOT NULL CHECK (trigger_type IN ('automatic','manual')),
  divergence_score    DECIMAL(4,3) NOT NULL,
  delta_report        JSONB NOT NULL,
  sample_old          TEXT NOT NULL,
  sample_new          TEXT NOT NULL,
  decision            VARCHAR(20) CHECK (decision IN ('update','keep','partial')),
  updated_dimensions  JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at          TIMESTAMPTZ
);
```

---

### pgvector Index on `identity_samples`

Add after `identity_samples` table creation (migration `0011`):

```sql
-- Add embedding column to identity_samples (pgvector — all vector search co-located on Railway PostgreSQL)
ALTER TABLE identity_samples ADD COLUMN embedding vector(1536);

-- Add style embedding to identity_profiles for divergence scoring
ALTER TABLE identity_profiles ADD COLUMN style_embedding vector(1536);

-- ANN index for fast similarity search per profile
CREATE INDEX ON identity_samples USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

---

## Updated Migration Order

```
0001 — users, refresh_tokens
0002 — user_consents
0003 — identity_profiles, identity_profile_snapshots
0004 — identity_vocabulary, identity_topics, identity_samples, identity_channel_profiles
0005 — channel_connections
0006 — pending_drafts
0007 — audit_logs
0008 — abuse_reports, biometric_assets
0009 — subscriptions
0010 — twin_briefings, sender_tiers, message_clusters, batch_sends,
        proactive_suggestions, proactive_preferences, surge_events, crisis_templates,
        twin_certificates, verification_log, channel_profile_mappings, style_checkpoints
0011 — pgvector extension + embedding columns on identity_samples + identity_profiles
```

---

*Status: Database Schema v1.1 — Updated 2026-04-27 with feature expansion tables and pgvector*
