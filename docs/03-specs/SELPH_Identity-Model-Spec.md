# SELPH — Identity Model Specification

> Version: 1.0
> Created: 2026-04-24
> Folder: 03-specs
> Status: Draft — Required before Phase 1 build

---

## Overview

The Identity Model is the core of SELPH. It is a structured representation of who a person is — their communication style, expertise, personality, and behavioral patterns — stored in a way that allows the Twin Engine to generate responses that sound authentically like them.

Every twin is a unique instantiation of this model. The model is built at onboarding and continuously updated through the feedback loop.

---

## Identity Model — Full Schema

### 1. Core Profile (PostgreSQL — structured)

```sql
identity_profiles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  version               INTEGER NOT NULL DEFAULT 1,       -- incremented on every update
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Name (used by Twin Engine prompt builder — p.first_name, p.last_name)
  first_name            VARCHAR(100) NOT NULL,
  last_name             VARCHAR(100) NOT NULL,

  -- Domain & Role
  domain                VARCHAR(100) NOT NULL,             -- "content creator", "software engineer"
  sub_domain            VARCHAR(100),                      -- "fitness", "travel", "backend dev"
  professional_title    VARCHAR(100),                      -- "YouTuber", "Freelance Designer"

  -- Communication Style
  tone                  VARCHAR(200) NOT NULL,             -- "casual, warm, humorous"
  formality_level       SMALLINT NOT NULL DEFAULT 3,       -- 1=very casual, 5=very formal
  avg_response_length   SMALLINT NOT NULL DEFAULT 80,      -- words
  response_length_min   SMALLINT NOT NULL DEFAULT 20,
  response_length_max   SMALLINT NOT NULL DEFAULT 200,
  emoji_usage           DECIMAL(3,2) NOT NULL DEFAULT 0.3, -- 0.0 to 1.0
  punctuation_style     VARCHAR(50) DEFAULT 'standard',    -- "minimal", "expressive", "standard"

  -- Greeting & Sign-off
  greeting_style        VARCHAR(100),                      -- "Hey!", "Hi there", "Yo"
  sign_off_style        VARCHAR(100),                      -- "Cheers", "Love", null

  -- Self-description
  personality_words     TEXT[] NOT NULL DEFAULT '{}',      -- ["warm", "direct", "funny"]
  bio_summary           TEXT,                              -- 2-3 sentence self-description

  -- Calibration
  approval_rate         DECIMAL(4,3) DEFAULT 0.0,          -- running approval rate 0.0-1.0
  total_drafts          INTEGER DEFAULT 0,
  total_approved        INTEGER DEFAULT 0,
  total_edited          INTEGER DEFAULT 0,
  total_rejected        INTEGER DEFAULT 0,
  trust_stage           SMALLINT DEFAULT 1,                -- 1, 2, or 3
  calibration_due_at    TIMESTAMPTZ,                       -- next weekly calibration date

  is_active             BOOLEAN DEFAULT true,
  UNIQUE(user_id)
)
```

---

### 2. Vocabulary Fingerprint (PostgreSQL — structured)

```sql
identity_vocabulary (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  word        VARCHAR(100) NOT NULL,
  frequency   INTEGER NOT NULL DEFAULT 1,       -- how often used in corpus
  weight      DECIMAL(4,3) NOT NULL DEFAULT 0.5, -- importance to identity 0.0-1.0
  source      VARCHAR(50) NOT NULL,              -- "instagram", "twitter", "email", "manual"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, word)
)

-- Index for fast vocabulary lookup
CREATE INDEX idx_vocabulary_profile ON identity_vocabulary(profile_id);
CREATE INDEX idx_vocabulary_weight ON identity_vocabulary(profile_id, weight DESC);
```

---

### 3. Topics (PostgreSQL — structured)

```sql
identity_topics (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  topic       VARCHAR(200) NOT NULL,
  type        VARCHAR(20) NOT NULL CHECK (type IN ('known', 'avoided', 'expert')),
  confidence  DECIMAL(3,2) DEFAULT 0.8,   -- how sure we are this is accurate
  source      VARCHAR(50),                -- "user_stated", "inferred", "content_analysis"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(profile_id, topic)
)
```

---

### 4. Sample Responses (PostgreSQL — structured)

```sql
identity_samples (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  channel         VARCHAR(50) NOT NULL,              -- "instagram_dm", "gmail", "twitter"
  incoming        TEXT NOT NULL,                     -- the message received
  response        TEXT NOT NULL,                     -- the actual response sent
  source          VARCHAR(20) NOT NULL,              -- "ingested", "approved_draft", "manual"
  quality_score   DECIMAL(3,2),                      -- rated by user (0.0-1.0) or null
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active       BOOLEAN DEFAULT true               -- false = excluded from few-shot pool
)

-- Keep top 50 samples per channel per profile for few-shot prompting
CREATE INDEX idx_samples_profile_channel ON identity_samples(profile_id, channel);
CREATE INDEX idx_samples_quality ON identity_samples(profile_id, quality_score DESC);
```

---

### 5. Identity Vectors (pgvector — on Railway PostgreSQL)

Each user has semantic vectors stored directly in PostgreSQL via the pgvector extension:

```
pgvector column: embedding VECTOR(1024) on identity_samples table
Dimensions: 1024 (Voyage AI voyage-3)
Metric: cosine (<=> operator)

Vector Types per user:
├── style_vector          → embedding of all approved drafts concatenated
├── topic_vector_{topic}  → embedding of content about each known topic
├── vocabulary_vector     → embedding of vocabulary fingerprint
└── sample_vector_{id}    → embedding of each sample response (on identity_samples rows)
```

```python
# pgvector similarity query — no external API hop, <5ms
results = db.query("""
    SELECT content FROM identity_samples
    WHERE profile_id = :profile_id
    ORDER BY embedding <=> :query_vector
    LIMIT 3
""", profile_id=profile.id, query_vector=embed(incoming_message))
```

---

### 6. Channel Profiles (PostgreSQL — per-channel style overrides)

```sql
identity_channel_profiles (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id        UUID NOT NULL REFERENCES identity_profiles(id) ON DELETE CASCADE,
  channel           VARCHAR(50) NOT NULL,            -- "instagram_dm", "gmail"
  tone_override     VARCHAR(200),                    -- channel-specific tone adjustment
  max_length        SMALLINT,                        -- character/word limit for channel
  emoji_override    DECIMAL(3,2),                    -- emoji usage for this channel
  format_hint       VARCHAR(100),                    -- "plain text", "markdown", "casual"
  is_active         BOOLEAN DEFAULT true,
  UNIQUE(profile_id, channel)
)
```

---

## Identity Capture Pipeline

### Phase 1 — Onboarding Questionnaire

Questions asked → stored directly in `identity_profiles`:

```
Q1: What do you do?                → domain, sub_domain, professional_title
Q2: Describe your communication style → tone, formality_level
Q3: Topics you talk about          → identity_topics (type=known)
Q4: Topics you never discuss       → identity_topics (type=avoided)
Q5: Typical response length        → avg_response_length
Q6: 3 words that describe you      → personality_words
Q7: How do you greet people?       → greeting_style
Q8: How do you sign off?           → sign_off_style
```

### Phase 2 — Content Ingestion

NLP analysis of ingested social content → populates vocabulary, samples, topics:

```python
def analyze_content_corpus(posts: list[str], channel: str, profile_id: str):
    # 1. Vocabulary extraction
    words = extract_top_words(posts, top_n=200)
    store_vocabulary(profile_id, words, source=channel)

    # 2. Topic detection
    topics = detect_topics(posts, method="zero_shot_classification")
    store_topics(profile_id, topics, source="content_analysis")

    # 3. Style metrics
    metrics = compute_style_metrics(posts)
    # metrics = { avg_length, emoji_rate, punctuation_style, formality_score }
    update_profile_metrics(profile_id, metrics)

    # 4. Sample extraction
    # Take top 20 posts as sample responses for few-shot prompting
    samples = select_best_samples(posts, top_n=20)
    store_samples(profile_id, samples, channel=channel, source="ingested")

    # 5. Generate and store style vector via pgvector
    style_vector = embed(concat(samples))
    db.execute("""
        UPDATE identity_samples SET embedding = :vector
        WHERE profile_id = :profile_id AND source = 'style_aggregate'
    """, vector=style_vector, profile_id=profile_id)
```

---

## Identity Update Loop (Feedback Learning)

Every time a user approves, edits, or rejects a draft:

```python
def update_identity_from_feedback(
    user_id: str,
    draft: str,
    user_action: str,              # "approved" | "edited" | "rejected"
    channel: str,
    edited_version: str | None = None,
    rejection_reason: str | None = None,
):
    profile = get_profile_by_user_id(user_id)

    if user_action == "approved":
        # Add to sample pool
        store_sample(profile_id, response=draft, source="approved_draft", channel=channel)
        profile.total_approved += 1

    elif user_action == "edited":
        # Store the edited version as a high-quality sample
        store_sample(profile_id, response=edited_version, quality_score=0.9,
                     source="approved_draft", channel=channel)
        # Extract what changed to refine style metrics
        diff = compute_diff(draft, edited_version)
        apply_style_corrections(profile_id, diff)
        profile.total_edited += 1

    elif user_action == "rejected":
        if rejection_reason:
            store_rejection_signal(profile_id, draft, rejection_reason)
        profile.total_rejected += 1

    # Update approval rate
    profile.total_drafts += 1
    profile.approval_rate = profile.total_approved / profile.total_drafts

    # Check trust stage advancement
    update_trust_stage(profile)

    # Regenerate style vector periodically (every 10 approvals)
    if profile.total_approved % 10 == 0:
        regenerate_style_vector(profile_id)

    save_profile(profile)
```

---

## Trust Stage Advancement Rules

```
Stage 1 → Stage 2:
  - total_drafts >= 50
  - approval_rate >= 0.85
  - minimum 2 weeks since activation

Stage 2 → Stage 3:
  - total_drafts >= 200
  - approval_rate >= 0.90
  - minimum 4 weeks in Stage 2
  - user explicitly enables Stage 3 in settings

Stage downgrade (any time):
  - approval_rate drops below 0.60 for 20+ consecutive drafts
  - user manually downgrades in settings
  - anomaly detected → auto-downgrade to Stage 1
```

---

## Identity Versioning

Every meaningful update to the profile creates a new version snapshot:

```sql
identity_profile_snapshots (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  UUID NOT NULL REFERENCES identity_profiles(id),
  version     INTEGER NOT NULL,
  snapshot    JSONB NOT NULL,    -- full profile_data at this version
  reason      VARCHAR(100),      -- "weekly_calibration", "bulk_edit", "auto_update", "user_edit"
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
```

This enables:
- Audit trail (legal requirement)
- Rollback if user doesn't like how their twin changed
- A/B testing twin versions for quality measurement

---

## Identity Confidence Score

A single score (0.0–1.0) representing how well the model knows the user:

```python
def compute_identity_confidence(profile) -> float:
    factors = {
        "sample_count":      min(profile.sample_count / 50, 1.0),   # 50 samples = full score
        "approval_rate":     profile.approval_rate,
        "topic_coverage":    min(len(profile.topics_known) / 10, 1.0),
        "vocab_coverage":    min(len(profile.vocabulary) / 100, 1.0),
        "days_active":       min(profile.days_active / 30, 1.0)
    }
    weights = [0.30, 0.30, 0.15, 0.10, 0.15]
    return sum(v * w for v, w in zip(factors.values(), weights))

# Displayed in app as: "Your twin knows you at 73%"
```

---

*Status: Identity Model Specification v1.0 — Ready for Phase 1 implementation*
