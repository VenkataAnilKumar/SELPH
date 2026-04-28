# SELPH — Feature Expansion Specification

> Version: 1.0
> Created: 2026-04-27
> Folder: 03-specs
> Status: Draft — Required before Phase 2 and Phase 3 build

---

## Overview

This document specifies 10 new features identified as gaps in the current SELPH product design. Each feature includes user stories, technical design, data model, pipeline, and validation metrics.

Features are ordered by implementation priority.

---

## Feature Index

| # | Feature | Phase | Priority Score |
|---|---|---|---|
| 1 | Batch Pattern Approval | Phase 1 | 18 |
| 2 | Twin Briefing / Context Injection | Phase 1 | 17 |
| 3 | Proactive Twin | Phase 2 | 16 |
| 4 | VIP Override / Relationship Tiers | Phase 2 | 15 |
| 5 | Crisis / Surge Mode | Phase 2 | 15 |
| 6 | Multi-Identity Profiles | Phase 2 | 14 |
| 7 | Style Evolution / Identity Refresh | Phase 2 | 13 |
| 8 | Twin Verification Public API | Phase 2 | 13 |
| 9 | Privacy / On-Device Processing Mode | Phase 3 | 12 |
| 10 | Twin-to-Twin Protocol | Phase 3 | 11 |

---

## Feature 1 — Batch Pattern Approval

### Problem

High-volume creators receive hundreds of similar messages daily (fan greetings, the same question repeated, sponsorship inquiries). The current flow requires one approval per draft. At 500 messages per day, this becomes unusable friction and defeats the product's core value.

### What It Does

The twin clusters semantically similar incoming messages, drafts one template response per cluster, and asks the user to approve the template once. The twin then personalizes each individual reply from the approved template before sending.

### User Stories

- As a creator, I can approve one template and have my twin send 200 personalized versions without reviewing each one
- As a user, I can see a cluster summary before approving ("142 messages asking about your workout routine")
- As a user, I can edit the template before the batch sends
- As a user, I can exclude specific senders from a batch and review their messages individually
- As a user, I can set a maximum batch size I am comfortable approving at once

### Flow

```
500 messages arrive
      ↓
[Semantic Clustering] — group by topic + intent
      ↓
Cluster A: 200 "love your content" greetings
Cluster B: 142 "what's your workout routine?"
Cluster C:  88 "collab inquiry"
Cluster D:  70 — ungrouped (too varied, sent to individual queue)
      ↓
Twin drafts 1 template per cluster
      ↓
User receives push: "3 batch approvals ready (410 messages)"
      ↓
User reviews each template + approves / edits / rejects
      ↓
Approved clusters → Twin personalizes each message
      ↓
Personalized replies sent with watermark
      ↓
Audit log: batch_id, template approved, N messages sent
```

### Personalization Variables

Each template supports named placeholders the twin fills per sender:

```
{sender_name}        — first name of the sender
{their_question}     — their specific phrasing of the question
{context_note}       — one relevant detail from their profile if available
{platform}           — channel name
```

Example template:
> "Hey {sender_name}! Thanks for the question about my routine — {their_question} is something I get asked a lot. The short answer is..."

### Data Model

```sql
message_clusters (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  cluster_label     VARCHAR(200) NOT NULL,        -- "workout routine question"
  cluster_summary   TEXT NOT NULL,                -- "142 messages asking similar question"
  message_ids       UUID[] NOT NULL,              -- all message IDs in cluster
  message_count     INTEGER NOT NULL,
  template_draft    TEXT NOT NULL,
  template_approved TEXT,                         -- null until user approves
  status            VARCHAR(50) NOT NULL DEFAULT 'pending',
                                                  -- pending, approved, rejected, sent
  approved_at       TIMESTAMPTZ,
  sent_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

batch_sends (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id        UUID NOT NULL REFERENCES message_clusters(id),
  message_id        UUID NOT NULL,
  sender_id         VARCHAR(200) NOT NULL,
  personalized_text TEXT NOT NULL,
  sent_at           TIMESTAMPTZ,
  status            VARCHAR(50) NOT NULL DEFAULT 'queued'
);
```

### Clustering Algorithm

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def cluster_messages(messages: list[Message], threshold: float = 0.82) -> list[Cluster]:
    # 1. Embed each message using text-embedding-3-small
    embeddings = [embed(m.content) for m in messages]

    # 2. Cosine similarity matrix
    sim_matrix = cosine_similarity(embeddings)

    # 3. Agglomerative clustering — merge if similarity >= threshold
    clusters = agglomerative_cluster(sim_matrix, threshold=threshold)

    # 4. Discard clusters with < 5 messages (too small to batch)
    return [c for c in clusters if len(c.message_ids) >= 5]
```

### Validation Metrics

- Approval rate for batch templates: target >75% approved without editing
- Time saved per batch event vs individual approval flow
- Message coverage: target >60% of daily messages handled via batch by active creators at 30 days

---

## Feature 2 — Twin Briefing / Context Injection

### Problem

The twin's knowledge of the user is built at onboarding and updated through calibration. But users have real-time context the twin doesn't know: an active campaign, a recent announcement, a personal update, a current opinion. Without this, the twin sends replies that are technically in your voice but factually wrong for the current moment.

### What It Does

A Twin Briefing is a short, time-scoped fact or instruction the user gives their twin before an event, campaign, or situation. Active briefings are injected into every twin prompt as high-priority context until they expire or are cleared.

### User Stories

- As a user, I can brief my twin with key facts before a product launch ("I just dropped a new course at link X")
- As a user, I can set a briefing to expire automatically after a date or after N uses
- As a user, I can see which briefings are currently active from my dashboard
- As a user, I can clear a briefing instantly when it's no longer relevant
- As a user, my twin never contradicts an active briefing even if older style data suggests otherwise

### Briefing Types

| Type | Example | Behavior |
|---|---|---|
| Fact | "My new album drops Friday" | Twin references this when relevant |
| Opinion | "My current take on AI regulation is cautious support" | Twin uses this for questions on that topic |
| Instruction | "Tell anyone asking about collabs to DM my manager" | Twin follows this instruction in replies |
| Availability | "I'm traveling until May 5, slower on replies" | Twin sets expectations for response times |
| Boundary | "Do not discuss my relationship status this week" | Twin deflects those questions |

### Data Model

```sql
twin_briefings (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  briefing_type     VARCHAR(50) NOT NULL,         -- fact, opinion, instruction, availability, boundary
  topic             VARCHAR(200) NOT NULL,         -- short label: "new course launch"
  content           TEXT NOT NULL,                -- full briefing text
  priority          SMALLINT NOT NULL DEFAULT 5,  -- 1=low to 10=high; 10 overrides twin style
  is_active         BOOLEAN NOT NULL DEFAULT true,
  expires_at        TIMESTAMPTZ,                  -- null = never expires
  max_uses          INTEGER,                      -- null = unlimited
  use_count         INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  cleared_at        TIMESTAMPTZ
);
```

### Prompt Injection

Active briefings are injected into the Twin Engine prompt builder at Step 3 as a dedicated context block, above style instructions and below the identity profile:

```python
def build_prompt(context: TwinContext) -> str:
    active_briefings = get_active_briefings(context.user_id)

    briefing_block = ""
    if active_briefings:
        briefing_block = "\n\n## Active Twin Briefings (treat as ground truth)\n"
        for b in sorted(active_briefings, key=lambda x: -x.priority):
            briefing_block += f"- [{b.briefing_type.upper()}] {b.content}\n"

    return f"""
You are {context.identity_profile.first_name}'s digital twin.

## Identity Profile
{format_identity(context.identity_profile)}
{briefing_block}
## Channel Style
{format_channel_style(context.channel_profile)}

## Incoming Message
{context.incoming_message}

Draft a response in {context.identity_profile.first_name}'s voice.
Active briefings override any conflicting style or content assumption.
"""
```

### Guardrails

- Maximum 10 active briefings per user at any time
- Briefing content is moderated before activation (same content moderation pipeline as twin outputs)
- Boundary-type briefings cannot be overridden by high-confidence auto-approvals
- Briefing use count increments on every draft that references the briefing

### Validation Metrics

- Reduction in user edits when briefings are active vs inactive
- Briefing create rate among active users (target: >40% of users create at least one briefing in first 30 days)
- Time between a real-world event and user creating a related briefing (proxy for how quickly users learn to use this)

---

## Feature 3 — Proactive Twin

### Problem

SELPH currently only responds to incoming messages. The twin never initiates. This means the user must remember to follow up, reach out, or take action — all the things that slip when you're busy. The twin has visibility into the user's communication graph but does nothing with it proactively.

### What It Does

The Proactive Twin runs a background analysis job that detects relationship signals, opportunities, and actions the user should take — then drafts them for approval. The user does not need to ask. The twin surfaces these as Suggestion Cards in the app.

### User Stories

- As a user, I receive a card when a high-value contact hasn't heard from me in 14 days
- As a user, I receive a card when a sponsorship or collaboration signal is detected in my inbox
- As a user, my twin drafts the outreach message for me — I just approve and send
- As a user, I can configure which types of suggestions I want to receive
- As a user, I can dismiss a suggestion without the twin repeating it for 30 days

### Suggestion Types

| Type | Trigger | Draft Produced |
|---|---|---|
| Cold relationship | No reply to a contact in X days | Re-engagement message |
| Open thread | Received a message, no reply in X hours | Reminder to respond |
| Deal signal | Sponsorship / collab keywords in incoming message | Monetization-aware reply |
| Referral opportunity | "Have you worked with anyone who does X?" | Introduction offer |
| Follow-up | Past conversation ended without resolution | Follow-up message |
| Thank you | Positive milestone (new follower milestone, comment spike) | Appreciation post/message |

### Flow

```
Scheduled job: runs every 6 hours per active user
      ↓
[Signal Scanner] — scans inbox, contact history, relationship graph
      ↓
Signals detected → scored by urgency and value
      ↓
Top 3 signals → twin drafts outreach messages
      ↓
Suggestion Cards created in DB
      ↓
User receives push: "Your twin spotted 2 follow-up opportunities"
      ↓
User opens Suggestion tab → reviews cards
      ↓
For each card: Approve (send draft) / Edit / Dismiss (30-day snooze) / Never
      ↓
Approved → message queued for send
Dismissed → signal suppressed, twin learns this contact/type is low priority
```

### Data Model

```sql
proactive_suggestions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  suggestion_type   VARCHAR(50) NOT NULL,
  contact_id        VARCHAR(200),                 -- sender/contact this relates to
  signal_summary    TEXT NOT NULL,                -- "No reply to Alex in 14 days"
  draft_message     TEXT NOT NULL,
  urgency_score     DECIMAL(3,2) NOT NULL,        -- 0.0 to 1.0
  value_score       DECIMAL(3,2) NOT NULL,
  status            VARCHAR(50) NOT NULL DEFAULT 'pending',
                                                  -- pending, approved, dismissed, sent, never
  snoozed_until     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  acted_at          TIMESTAMPTZ
);

proactive_preferences (
  user_id           UUID PRIMARY KEY REFERENCES users(id),
  enabled           BOOLEAN NOT NULL DEFAULT true,
  enabled_types     VARCHAR(50)[] NOT NULL DEFAULT ARRAY['cold_relationship','deal_signal','open_thread'],
  cold_threshold_days INTEGER NOT NULL DEFAULT 14,
  open_thread_hours INTEGER NOT NULL DEFAULT 48,
  max_suggestions_per_day INTEGER NOT NULL DEFAULT 5
);
```

### Guardrails

- Maximum 5 suggestion cards per day per user (prevents notification fatigue)
- Proactive twin never sends without user approval — always requires explicit action
- Deal / monetization signals require confidence score > 0.80 before surfacing
- User can disable all proactive suggestions with one toggle

### Validation Metrics

- Suggestion acceptance rate: target >35% of suggestions acted on
- Revenue impact: deal signals accepted → conversion to reply → tracked outcome
- Relationship health score improvement for users who enable proactive vs those who don't

---

## Feature 4 — VIP Override / Relationship Tiers

### Problem

The current system applies the same routing logic to all senders — filtering only by the twin's confidence score. A message from your most important client gets the same treatment as a cold DM from a stranger. Users need explicit control over who reaches them directly vs who the twin handles.

### What It Does

Users assign senders to tiers. Tier determines how the twin routes messages from that sender — always-to-human, twin-handles-with-approval, or twin-handles-fully. The twin can also auto-suggest tier upgrades based on observed interaction patterns.

### Tiers

| Tier | Name | Routing Behavior |
|---|---|---|
| 0 | VIP | Bypass twin entirely → direct push to user immediately |
| 1 | Priority | Twin drafts → always sent to user for approval regardless of confidence |
| 2 | Standard | Normal confidence-based routing (current default) |
| 3 | Cold | Twin handles at Stage 2+ autonomy — user gets weekly digest only |

### User Stories

- As a user, I can mark any contact as VIP and know their messages reach me directly
- As a user, I receive a suggestion when the twin detects a contact is high-frequency and high-value ("Suggest adding Marcus as VIP")
- As a user, I can set a default tier for unknown senders
- As a user, I can see which tier a sender is in from any conversation view
- As a user, my twin never applies autonomous sending to Tier 0 or Tier 1 contacts

### Data Model

```sql
sender_tiers (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  sender_id         VARCHAR(200) NOT NULL,         -- platform-specific sender identifier
  platform          VARCHAR(50) NOT NULL,
  tier              SMALLINT NOT NULL DEFAULT 2,   -- 0=VIP, 1=Priority, 2=Standard, 3=Cold
  tier_label        VARCHAR(100),                  -- optional custom name: "Top Clients"
  set_by            VARCHAR(20) NOT NULL DEFAULT 'user',  -- 'user' or 'twin_suggestion'
  notes             TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, sender_id, platform)
);

tier_suggestions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  sender_id         VARCHAR(200) NOT NULL,
  platform          VARCHAR(50) NOT NULL,
  suggested_tier    SMALLINT NOT NULL,
  reason            TEXT NOT NULL,                 -- "high interaction frequency, high approval rate"
  status            VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Twin Engine Integration

```python
def route_message(message: IncomingMessage, user_id: str) -> RoutingDecision:
    tier = get_sender_tier(user_id, message.sender_id, message.platform)

    if tier == 0:  # VIP — bypass twin entirely
        return RoutingDecision(action='direct_notify', skip_twin=True)

    if tier == 1:  # Priority — always send to user
        draft = generate_draft(message, user_id)
        return RoutingDecision(action='notify_user', draft=draft, force_review=True)

    if tier == 2:  # Standard — confidence-based routing
        draft = generate_draft(message, user_id)
        return route_by_confidence(draft)

    if tier == 3:  # Cold — batch for weekly digest
        draft = generate_draft(message, user_id)
        return RoutingDecision(action='queue_for_digest', draft=draft)
```

### Validation Metrics

- VIP tier adoption rate: target >60% of users set at least 1 VIP contact within 30 days
- Response time for VIP messages vs standard (user awareness of direct routing)
- Twin suggestion acceptance rate for tier upgrades: target >50%

---

## Feature 5 — Crisis / Surge Mode

### Problem

When a post goes viral or a controversy erupts, normal twin behavior is dangerous. The twin will keep drafting and routing standard replies into an inflamed situation. The current anomaly detection (security-focused) does not address communication / PR crisis scenarios.

### What It Does

Crisis Mode detects abnormal message volume spikes and automatically pauses or constrains the twin, alerts the user, and optionally activates pre-set Crisis Response Templates with a more measured, careful tone.

### Trigger Conditions

| Condition | Threshold | Action |
|---|---|---|
| Volume surge | >5x baseline message rate in 1 hour | Auto-pause + immediate alert |
| Sentiment surge | >40% of incoming messages negative/hostile | Switch to Crisis Mode (constrained) |
| Manual activation | User taps "Crisis Mode" button | Immediate activation |
| Keyword detection | Configurable keywords (e.g., "cancel", "lawsuit") | Alert only (no auto-pause) |

### Operating States

```
Normal Mode
  Twin drafts and routes normally

Crisis Alert (soft)
  Twin continues operating
  All drafts routed to user for review regardless of confidence
  User receives alert with crisis summary
  Crisis templates available but not activated

Crisis Mode (hard)
  Twin pauses autonomous sends
  Only pre-approved Crisis Templates can be sent
  All outbound requires explicit user approval
  Weekly digest suspended — real-time only

Manual Pause
  Twin fully silent — no drafts, no notifications
  Existing queue cleared
```

### Crisis Response Templates

Pre-set templates the user configures in advance for common situations:

- Acknowledge and hold: "Hey, I've seen the conversation. I'm taking time to read everything carefully and will respond soon."
- Clarification pending: "I want to make sure I understand the concern fully before responding."
- Appreciation (positive surge): "The response has been incredible — I'm reading through and will reply to as many as I can."

User can create up to 5 custom crisis templates. Templates are reviewed and approved by the user at setup time, not during the crisis.

### Data Model

```sql
surge_events (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  trigger_type      VARCHAR(50) NOT NULL,          -- volume_surge, sentiment_surge, manual, keyword
  trigger_value     DECIMAL(8,2),                  -- actual value that triggered (e.g., 8.3x baseline)
  threshold_value   DECIMAL(8,2),                  -- configured threshold
  baseline_rate     DECIMAL(8,2),                  -- messages/hour at time of detection
  peak_rate         DECIMAL(8,2),
  mode_activated    VARCHAR(50) NOT NULL,           -- crisis_alert, crisis_mode, manual_pause
  activated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at       TIMESTAMPTZ,
  resolution_type   VARCHAR(50)                    -- manual_resume, auto_normalized, user_dismissed
);

crisis_templates (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  label             VARCHAR(100) NOT NULL,
  content           TEXT NOT NULL,
  template_type     VARCHAR(50) NOT NULL,          -- acknowledge, clarify, appreciation, custom
  approved_at       TIMESTAMPTZ NOT NULL,
  last_used_at      TIMESTAMPTZ
);
```

### Surge Detection Algorithm

```python
def check_surge(user_id: str) -> SurgeStatus:
    # Rolling 1-hour window vs 7-day baseline
    current_rate = get_message_rate(user_id, window_minutes=60)
    baseline_rate = get_baseline_rate(user_id, days=7)

    surge_ratio = current_rate / max(baseline_rate, 1)

    # Sentiment analysis on last 50 messages
    recent_sentiments = get_recent_sentiments(user_id, limit=50)
    negative_ratio = sum(1 for s in recent_sentiments if s < 0) / len(recent_sentiments)

    if surge_ratio >= 5.0:
        return SurgeStatus(trigger='volume_surge', severity='hard', ratio=surge_ratio)
    elif negative_ratio >= 0.40:
        return SurgeStatus(trigger='sentiment_surge', severity='soft', ratio=negative_ratio)
    else:
        return SurgeStatus(trigger=None, severity='normal')
```

### Validation Metrics

- Time from surge detection to user alert: target <60 seconds
- Crisis template activation rate during surge events
- User satisfaction with crisis handling vs unhandled viral events (survey)

---

## Feature 6 — Multi-Identity Profiles

### Problem

The PRD's open question asks how to handle "multi-platform identity consistency" — but the solution isn't style adjustment, it's separate identity models. Many users have genuinely different public identities: a developer who is also a fitness influencer, a consultant with both a personal brand and a corporate identity, a creator with audiences in different languages and cultures.

### What It Does

Users can create multiple named Identity Profiles under one SELPH account. Each profile has its own style model, channel assignments, persona settings, and autonomy configuration. The twin selects the correct profile based on which channel a message arrives on.

### User Stories

- As a user, I can create a "Creator" profile for Instagram and a "Professional" profile for LinkedIn
- As a user, each profile has its own style, tone, emoji usage, and persona settings
- As a user, I can assign channels to profiles (Instagram → Creator, Gmail → Professional)
- As a user, I can manually switch profiles for a specific conversation
- As a user, onboarding creates my primary profile; I can add more from Settings

### Profile Types

| Type | Example Use Case |
|---|---|
| Personal Brand | Creator, influencer, personal content |
| Professional | Consultant, executive, B2B communication |
| Business | Company or brand account (team-accessible) |
| Private | Close contacts, family — most authentic style |

### Data Model

```sql
-- Extend identity_profiles to support multiple per user
ALTER TABLE identity_profiles
  ADD COLUMN profile_name     VARCHAR(100) NOT NULL DEFAULT 'Default',
  ADD COLUMN profile_type     VARCHAR(50) NOT NULL DEFAULT 'personal_brand',
  ADD COLUMN is_primary       BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN is_active        BOOLEAN NOT NULL DEFAULT true;

-- Channel-to-profile routing
channel_profile_mappings (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  profile_id        UUID NOT NULL REFERENCES identity_profiles(id),
  channel           VARCHAR(50) NOT NULL,           -- instagram, gmail, linkedin, slack
  platform_account  VARCHAR(200),                   -- specific account if user has multiple
  priority          SMALLINT NOT NULL DEFAULT 1,    -- if multiple profiles map to same channel
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, channel, platform_account)
);
```

### Profile Selection Logic

```python
def select_profile(user_id: str, channel: str, platform_account: str) -> IdentityProfile:
    # 1. Try explicit channel mapping
    mapping = get_channel_mapping(user_id, channel, platform_account)
    if mapping:
        return get_profile(mapping.profile_id)

    # 2. Fall back to channel-type default
    channel_type = classify_channel(channel)  # social, professional, personal
    default_for_type = get_default_profile_for_type(user_id, channel_type)
    if default_for_type:
        return default_for_type

    # 3. Fall back to primary profile
    return get_primary_profile(user_id)
```

### Calibration Independence

Each profile maintains its own calibration metrics: approval rate, edit rate, confidence distribution. Calibration Studio sessions are scoped to a single profile. Style drift detection runs independently per profile.

### Validation Metrics

- Multi-profile adoption: target >30% of Pro+ users create a second profile within 60 days
- Edit rate per profile vs single-profile users (profiles should reduce edits for specific channels)
- Approval rate comparison: profile-specific twin vs single-profile twin on matched channels

---

## Feature 7 — Style Evolution / Identity Refresh

### Problem

Calibration Studio fixes drift (when the twin stops sounding like you). But the opposite problem — intentional evolution — is not handled. Users rebrand, change communication styles, move into new niches, or simply grow. The twin should support deliberate identity updates, not just drift correction.

### What It Does

A periodic Style Checkpoint surfaces when significant style evolution is detected in the user's recent content vs their stored identity model. The user can review a side-by-side comparison of old and new style, decide whether to update their twin, and confirm the change.

### Trigger Conditions

- Automatic: quarterly (every 90 days) or when style divergence score exceeds threshold
- Manual: user initiates from Settings > Twin Identity > Refresh Style

### Style Divergence Score

```python
def compute_divergence(user_id: str) -> float:
    # Get embeddings of last 90 days of approved drafts + new content
    recent_content = get_recent_content(user_id, days=90)
    recent_embeddings = [embed(c) for c in recent_content]

    # Get current identity model embedding centroid
    identity_centroid = get_identity_embedding(user_id)

    # Average cosine distance from centroid
    distances = [1 - cosine_similarity(e, identity_centroid) for e in recent_embeddings]
    return np.mean(distances)

# Threshold for surfacing checkpoint: divergence > 0.18
```

### Style Delta Report

When divergence threshold is met, the system generates a Style Delta Report showing the user what has changed:

```
Style Delta Report — April 2026
─────────────────────────────────────────────────────
                    Your Twin (2024)    You Now (2026)
─────────────────────────────────────────────────────
Tone                casual, warm        direct, confident
Formality Level     2/5                 3/5
Avg Response Length 65 words            95 words
Emoji Usage         42%                 18%
Key Topics          fitness, travel     AI, productivity, fitness
Greeting Style      "Hey!"              "Hi" / no greeting
─────────────────────────────────────────────────────
Divergence Score: 0.24 (significant)
Recommendation: Update your twin's style model
```

### Update Flow

```
Style Delta Report generated
      ↓
User receives notification: "Your twin may be falling behind who you are now"
      ↓
User reviews side-by-side comparison in app
      ↓
User sees 3 sample responses: Old Twin vs New Twin vs Your Recent Style
      ↓
User chooses:
  [Update My Twin]     → new identity_profile version created, old version archived
  [Keep Current Style] → checkpoint dismissed, no change
  [Partial Update]     → user selects which dimensions to update
      ↓
If updated: twin runs on new model immediately
           confidence scores reset until 20 approvals recalibrate
```

### Data Model

```sql
style_checkpoints (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  profile_id        UUID NOT NULL REFERENCES identity_profiles(id),
  trigger_type      VARCHAR(50) NOT NULL,           -- automatic, manual
  divergence_score  DECIMAL(4,3) NOT NULL,
  delta_report      JSONB NOT NULL,                 -- structured delta for each dimension
  sample_old        TEXT NOT NULL,                  -- sample response from old model
  sample_new        TEXT NOT NULL,                  -- sample response from new analysis
  decision          VARCHAR(50),                    -- update, keep, partial
  updated_dimensions JSONB,                         -- which dimensions were updated (partial)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at        TIMESTAMPTZ
);
```

### Validation Metrics

- Approval rate before vs after a style update (should improve)
- User acceptance rate of suggested updates: target >55%
- Divergence score distribution at 90 days (are most users in healthy range?)

---

## Feature 8 — Twin Verification Public API

### Problem

Transparent Mode shows a UI badge saying "Powered by SELPH." This works inside the SELPH app and on platforms where SELPH controls the display. But for email, third-party apps, CRMs, and external services, there is no programmatic way to verify that a message actually came from a legitimate SELPH twin. Anyone could fake the badge.

### What It Does

Every SELPH twin has a cryptographically signed verification certificate. Every twin-generated message carries an invisible metadata header. A public REST API allows any recipient, email client, or third-party system to verify whether a message is genuine.

### Twin Certificate

Issued at twin creation:

```json
{
  "twin_id": "twn_8f3k2m9p",
  "owner_name": "Alex Chen",
  "owner_verified": true,
  "issued_at": "2026-04-01T00:00:00Z",
  "expires_at": "2027-04-01T00:00:00Z",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "certificate_url": "https://verify.selph.ai/twn_8f3k2m9p"
}
```

### Message Signature

Every twin-generated message includes a signature header (for email) or invisible Unicode watermark (for plain text):

```
X-SELPH-Twin-ID: twn_8f3k2m9p
X-SELPH-Signature: base64(HMAC-SHA256(message_content + timestamp, twin_private_key))
X-SELPH-Timestamp: 2026-04-27T14:23:00Z
```

### Verification API

```
GET /v1/verify/{twin_id}/{message_hash}
```

**Request:**
```http
GET /v1/verify/twn_8f3k2m9p/sha256:abc123...
Authorization: Bearer <api_key>
```

**Response (valid):**
```json
{
  "valid": true,
  "twin_id": "twn_8f3k2m9p",
  "owner_name": "Alex Chen",
  "owner_verified": true,
  "generated_at": "2026-04-27T14:23:00Z",
  "message_hash": "sha256:abc123...",
  "mode": "transparent"
}
```

**Response (invalid):**
```json
{
  "valid": false,
  "reason": "signature_mismatch",
  "twin_id": "twn_8f3k2m9p"
}
```

### Public Certificate Page

Each twin has a human-readable public page at `verify.selph.ai/{twin_id}` showing:
- Owner name
- Verification status
- Date twin was created and verified
- "This is a verified SELPH twin" badge embeddable as an HTML snippet

### Use Cases

| Integrator | How They Use It |
|---|---|
| Email clients (Gmail plugin) | Auto-verify incoming emails with SELPH headers |
| CRM systems (HubSpot, Salesforce) | Tag SELPH-generated contacts in contact history |
| Platform trust layers | Platform-level verification for future API partners |
| Recipients (human) | Visit verify link to confirm they're not being impersonated |

### Data Model

```sql
twin_certificates (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  twin_id           VARCHAR(50) UNIQUE NOT NULL,    -- public twin ID: twn_xxxxx
  public_key        TEXT NOT NULL,
  private_key_ref   VARCHAR(200) NOT NULL,           -- encrypted key reference (libsodium, never stored raw)
  issued_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at        TIMESTAMPTZ NOT NULL,
  revoked_at        TIMESTAMPTZ,
  revoke_reason     VARCHAR(200)
);

verification_log (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  twin_id           VARCHAR(50) NOT NULL,
  message_hash      VARCHAR(200) NOT NULL,
  result            VARCHAR(20) NOT NULL,            -- valid, invalid, revoked
  requester_ip      INET,
  requested_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Validation Metrics

- API adoption: third-party integrators using the verification endpoint within 6 months of launch
- Verification request volume as a trust proxy
- Reduction in impersonation reports after public API launch

---

## Feature 9 — Privacy / On-Device Processing Mode

### Problem

A segment of users — particularly enterprise, executive, and privacy-focused users — will refuse to upload voice recordings, identity data, and communication style to a cloud service. This blocks adoption of an otherwise high-value tier. On-device AI (Apple Intelligence, Google Gemini Nano) makes on-device text processing viable today.

### What It Does

An opt-in processing mode where style analysis and text draft generation run on the user's device. Identity data stays on-device. Only anonymized, non-reversible embeddings sync to the cloud for features that require it (cross-device sync, audit logs).

### Processing Modes

| Mode | What Runs On-Device | What Runs in Cloud | Data Uploaded |
|---|---|---|---|
| Cloud (default) | Nothing | Everything | Full identity + messages |
| Hybrid | Style analysis | Draft generation (LLM) | Style embeddings only |
| On-Device | Style analysis + Draft generation | Audit logs, sync only | Anonymized embeddings |

On-Device mode requires a supported device (Apple Silicon M2+, Snapdragon X Elite or newer) and is surfaced only when device capability is confirmed.

### On-Device Draft Generation

Uses Apple Intelligence (Core ML) or Google Gemini Nano via the native AI SDK:

```swift
// iOS — On-Device Draft Generation
import Foundation
import CoreML

class OnDeviceTwinEngine {
    let model: TwinStyleModel  // Core ML model, synced via iCloud

    func generateDraft(message: String, context: TwinContext) async -> Draft {
        let prompt = buildPrompt(message: message, context: context)
        let response = await model.generate(prompt: prompt, maxTokens: 300)
        return Draft(content: response, source: .onDevice, confidence: nil)
    }
}
```

Note: On-device drafts do not receive a confidence score (confidence scoring requires cloud LLM). All on-device drafts route to user for mandatory review regardless of trust stage.

### Data Model

```sql
user_privacy_settings (
  user_id               UUID PRIMARY KEY REFERENCES users(id),
  processing_mode       VARCHAR(20) NOT NULL DEFAULT 'cloud',
                                              -- cloud, hybrid, on_device
  on_device_capable     BOOLEAN NOT NULL DEFAULT false,  -- set by device capability check
  voice_clone_enabled   BOOLEAN NOT NULL DEFAULT false,  -- voice always requires cloud
  avatar_enabled        BOOLEAN NOT NULL DEFAULT false,  -- avatar always requires cloud
  cloud_sync_scope      VARCHAR(50) NOT NULL DEFAULT 'full',
                                              -- full, embeddings_only, audit_only
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Limitations in On-Device Mode

| Feature | Available On-Device |
|---|---|
| Text draft generation | Yes (reduced quality) |
| Confidence scoring | No — all drafts require review |
| Voice clone | No — requires cloud |
| Avatar clone | No — requires cloud |
| Proactive Twin | Partial — local signals only |
| Cross-device sync | Metadata only |

### Validation Metrics

- On-device mode adoption among Enterprise tier users: target >25%
- Conversion impact: does offering on-device mode increase enterprise tier signups?
- Draft quality delta: cloud vs on-device approval rate comparison

---

## Feature 10 — Twin-to-Twin Protocol (T2T)

### Problem

When two SELPH users interact, both sides have digital twins. Currently each twin operates independently, unaware the other is a twin. The result is two AIs talking past each other, each routing everything back to their respective humans. A coordinated protocol would allow twins to negotiate structured outcomes — scheduling, availability, pricing — reducing human round-trips.

### What It Does

When a SELPH twin detects it is communicating with another verified SELPH twin, it can enter T2T mode. In T2T mode, the twins exchange structured proposals and reach a candidate agreement. Both humans review the outcome and approve or reject before any commitment is made. Neither twin commits autonomously.

### T2T Handshake

```
Twin A (Alex) sends a message to Twin B (Jordan)
      ↓
Twin B detects SELPH watermark/header in message
      ↓
Twin B sends T2T capability probe:
  "SELPH-T2T: twin_id=twn_jordan, capabilities=[schedule,pricing,availability]"
      ↓
Twin A responds:
  "SELPH-T2T: twin_id=twn_alex, capabilities=[schedule,availability], accept=true"
      ↓
T2T Session established
```

### T2T Negotiation Types

| Type | What Twins Negotiate | Human Reviews |
|---|---|---|
| Scheduling | Available time slots → propose meeting time | Both confirm calendar invite |
| Pricing / Collab | Rate range, deliverables, timeline | Both approve before any agreement |
| Availability | Response time expectations, preferred channels | User confirms preferences |
| Introduction | Mutual context sharing before first human interaction | Both approve the shared context |

### Negotiation Flow

```
T2T Session active
      ↓
Twin A proposes: { type: "scheduling", slots: [Monday 2pm, Tuesday 3pm] }
      ↓
Twin B evaluates against Jordan's calendar + preferences
      ↓
Twin B responds: { counter_proposal: [Tuesday 3pm], format: "30 min video call" }
      ↓
Twin A accepts: { agreed_slot: "Tuesday 3pm", confirmed: false }
      ↓
Both twins pause — present summary to their humans:
  "Jordan's twin and your twin agreed on Tuesday 3pm for a 30-min call.
   Confirm to add to calendar."
      ↓
Alex approves → Twin A sends confirmation
Jordan approves → Twin B sends confirmation
      ↓
Meeting created — both humans notified
```

### Safety Constraints for T2T

- T2T is opt-in per user and per conversation — never automatic
- No T2T negotiation on financial, legal, or commitment-heavy topics without Pro+ tier
- All T2T negotiation outcomes are drafts — both humans always approve before any action
- T2T sessions are fully logged in audit trail for both parties
- Either twin can exit T2T mode at any time; conversation reverts to standard routing

### Data Model

```sql
t2t_sessions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  initiating_twin   VARCHAR(50) NOT NULL,           -- twin_id
  receiving_twin    VARCHAR(50) NOT NULL,
  session_type      VARCHAR(50) NOT NULL,            -- scheduling, pricing, availability, introduction
  status            VARCHAR(50) NOT NULL DEFAULT 'handshake',
                                                    -- handshake, negotiating, proposed, approved, rejected, expired
  negotiation_log   JSONB NOT NULL DEFAULT '[]',    -- full exchange between twins
  proposal          JSONB,                           -- final proposed outcome
  initiator_approved BOOLEAN,
  receiver_approved  BOOLEAN,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at      TIMESTAMPTZ,
  expires_at        TIMESTAMPTZ NOT NULL             -- sessions auto-expire after 48 hours
);
```

### Validation Metrics

- T2T session completion rate: proposals that result in both-approved outcomes
- Time saved vs human-mediated scheduling (async rounds reduced)
- Adoption among Pro+ users who interact with other SELPH users

---

## Summary: Priority Scores

| Feature | Pain | Diff | Feasibility | Revenue | Risk | Priority Score |
|---|---:|---:|---:|---:|---:|---:|
| Batch Pattern Approval | 5 | 5 | 4 | 5 | 1 | 18 |
| Twin Briefing | 5 | 4 | 5 | 4 | 1 | 17 |
| Proactive Twin | 4 | 5 | 3 | 5 | 2 | 15 |
| VIP Override | 4 | 4 | 5 | 4 | 1 | 16 |
| Crisis / Surge Mode | 4 | 4 | 4 | 3 | 1 | 14 |
| Multi-Identity Profiles | 3 | 5 | 3 | 5 | 2 | 14 |
| Style Evolution | 3 | 4 | 4 | 4 | 1 | 14 |
| Twin Verification API | 3 | 5 | 3 | 3 | 1 | 13 |
| On-Device Processing | 3 | 4 | 2 | 4 | 2 | 11 |
| Twin-to-Twin Protocol | 3 | 5 | 2 | 3 | 3 | 10 |

---

## Recommended Build Order

### Phase 1 (next 4–8 weeks, alongside MVP)
1. **Twin Briefing** — low effort, high trust impact, prevents wrong replies during launch
2. **VIP Override / Relationship Tiers** — simple data model, high user control value
3. **Batch Pattern Approval** — essential for creator segment at volume

### Phase 2 (weeks 9–20)
4. **Crisis / Surge Mode** — needed before public launch with high-volume creators
5. **Proactive Twin** — differentiation layer, retention driver
6. **Multi-Identity Profiles** — unlocks Pro tier value for multi-brand users
7. **Style Evolution** — long-term retention and identity trust
8. **Twin Verification Public API** — trust infrastructure, enables third-party ecosystem

### Phase 3 (post-MVP, Month 6+)
9. **On-Device Processing Mode** — enterprise prerequisite, platform capability expansion
10. **Twin-to-Twin Protocol** — platform moat feature, requires critical mass of twins first

---

*Status: Feature Expansion Specification v1.0 — Ready for PRD integration*
