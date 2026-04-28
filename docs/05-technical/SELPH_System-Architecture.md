# SELPH — System Architecture

> Version: 1.1
> Created: 2026-04-24
> Updated: 2026-04-27
> Folder: 05-technical
> Status: Active — MVP Architecture. Deployed on Railway + Cloudflare R2.

---

## Overview

This document describes how all SELPH components connect end-to-end — from a message arriving on Instagram to a push notification reaching the user's phone, and from an approval tap back to sending the final message.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL WORLD                               │
│   Instagram DM  ·  Gmail  ·  Twitter DM  ·  WhatsApp               │
└────────────────────────┬────────────────────────────────────────────┘
                         │ Webhooks
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SELPH BACKEND (FastAPI on Railway)             │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │ Channel      │   │ Auth &       │   │ Consent &            │   │
│  │ Adapter      │   │ Identity     │   │ Compliance           │   │
│  │ Layer        │   │ Service      │   │ Service              │   │
│  └──────┬───────┘   └──────────────┘   └──────────────────────┘   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   TWIN ENGINE (LangGraph)                    │  │
│  │                                                              │  │
│  │  Context    Channel    Prompt     Draft      Confidence      │  │
│  │  Loader  →  Router  →  Builder →  Generator → Scorer        │  │
│  │                                       │                     │  │
│  │  Content    Approval                  │                     │  │
│  │  Moderator← Router  ←────────────────┘                     │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │ Task Queue   │   │ Notification │   │ Audit Log            │   │
│  │ (Redis +     │   │ Service      │   │ Service              │   │
│  │  Celery)     │   │ (Firebase)   │   │                      │   │
│  └──────────────┘   └──────┬───────┘   └──────────────────────┘   │
└──────────────────────┬─────┼────────────────────────────────────────┘
                       │     │ Push notification
                       │     ▼
                       │  ┌─────────────────────────────────────────────┐
                       │  │         SELPH MOBILE APP (React Native)     │
                       │  │                                             │
                       │  │  Notification → Approval UI                 │
                       │  │  [Approve / Edit / Reject]                  │
                       │  │  Settings · Twin Profile · Consent          │
                       │  └──────────────────┬──────────────────────────┘
                       │                     │ Human decision (REST API)
                       │                     ▼
                       │  ┌─────────────────────────────────────────────┐
                       │  │    SELPH WEB APP (Next.js on Vercel)        │
                       │  │                                             │
                       │  │  Twin Dashboard · Draft Review              │
                       │  │  Identity Profile · Audit Log               │
                       │  │  Settings · Channel Management              │
                       │  │  REST API + WebSocket ← → FastAPI backend   │
                       │  └─────────────────────────────────────────────┘
                       │
                       ▼ (Cloudflare DNS → selph.ai)
              ┌────────────────────────────────┐
              │  LANDING PAGE (Next.js/Vercel) │
              │                                │
              │  selph.ai — marketing site     │
              │  Waitlist · Pricing · Docs     │
              │  "Start for free" → Web App    │
              └────────────────────────────────┘
```

---

## Component Map

### 1. Channel Adapter Layer

Translates platform-specific webhooks into a normalized `IncomingMessage` object.

```python
@dataclass
class IncomingMessage:
    id: str
    user_id: str               # SELPH user who owns this twin
    channel: str               # "instagram_dm" | "gmail" | "twitter_dm" | "whatsapp"
    sender_id: str             # platform-specific sender ID
    sender_name: str
    content: str
    attachments: list[str]     # URLs of any attached media
    received_at: datetime
    platform_message_id: str   # platform's own message ID for deduplication
```

**Per-channel adapters:**

| Channel | Trigger | Auth Method |
|---|---|---|
| Instagram DM | Webhooks (Meta Graph API v21+) | OAuth 2.0, Business Account required |
| Gmail | Google Pub/Sub push (not polling) | OAuth 2.0, Gmail API v1 |
| Twitter DM | Account Activity API webhooks | OAuth 1.0a |
| WhatsApp | WhatsApp Business API webhooks | WhatsApp Business Account |

---

### 2. Twin Engine (LangGraph StateGraph)

The core AI pipeline. Defined as a `StateGraph` with `TwinEngineState`:

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver  # MVP only — replaced by RedisSaver in Phase 2+

workflow = StateGraph(TwinEngineState)

# Nodes
workflow.add_node("load_context",     load_context_node)
workflow.add_node("route_channel",    route_channel_node)
workflow.add_node("build_prompt",     build_prompt_node)
workflow.add_node("generate_draft",   generate_draft_node)
workflow.add_node("score_confidence", score_confidence_node)
workflow.add_node("moderate",         moderate_node)
workflow.add_node("route_approval",   route_approval_node)
workflow.add_node("await_human",      await_human_node)     # interrupt() here
workflow.add_node("process_decision", process_decision_node)
workflow.add_node("flag_for_review",  flag_for_review_node)  # notifies user, logs flags

# Edges
workflow.set_entry_point("load_context")
workflow.add_edge("load_context",     "route_channel")
workflow.add_edge("route_channel",    "build_prompt")
workflow.add_edge("build_prompt",     "generate_draft")
workflow.add_edge("generate_draft",   "score_confidence")
workflow.add_edge("score_confidence", "moderate")
workflow.add_conditional_edges(
    "moderate",
    lambda s: "route_approval" if s["moderation_passed"] else "flag_for_review",
    {"route_approval": "route_approval", "flag_for_review": "flag_for_review"}
)
workflow.add_edge("route_approval",   "await_human")
workflow.add_edge("await_human",      "process_decision")
workflow.add_edge("process_decision", END)
workflow.add_edge("flag_for_review",  END)

# flag_for_review_node: stores draft as FLAGGED, sends push notification to user
# "A message arrived but your twin flagged it for safety review — tap to handle manually"

# Human-in-the-loop: persist state until user decides
# MVP: PostgresSaver
checkpointer = PostgresSaver.from_conn_string(settings.DATABASE_URL)
# Future: Switch to RedisSaver for higher concurrency
# checkpointer = RedisSaver.from_conn_string(REDIS_URL, ttl={"default": 86400 * 7})
graph = workflow.compile(checkpointer=checkpointer, interrupt_before=["await_human"])
```

---

### 3. Storage Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                │
│                                                                     │
│  PostgreSQL (primary relational DB)                                 │
│  ├── users                    — accounts, auth                     │
│  ├── identity_profiles        — core twin profile                  │
│  ├── identity_vocabulary      — word frequency                     │
│  ├── identity_topics          — known/avoided/expert topics        │
│  ├── identity_samples         — few-shot examples                  │
│  ├── identity_channel_profiles— per-channel overrides             │
│  ├── identity_profile_snapshots— versioned profile history        │
│  ├── user_consents            — consent audit trail               │
│  ├── pending_drafts           — drafts awaiting human approval    │
│  ├── audit_logs               — all actions logged               │
│  └── langgraph_checkpoints    — LangGraph interrupted state       │
│                                                                     │
│  pgvector (on Railway PostgreSQL)                                   │
│  └── embedding VECTOR(1024) on identity_samples                   │
│      ├── style vectors per user                                    │
│      ├── topic vectors per user                                    │
│      └── sample vectors per approved response                      │
│                                                                     │
│  Redis (cache + queue)                                              │
│  ├── Session cache (15-min TTL)                                    │
│  ├── Identity profile cache (5-min TTL)                            │
│  └── Celery task queue                                             │
│                                                                     │
│  Cloudflare R2 (object storage)                                     │
│  ├── users/{user_id}/voice/   — encrypted voice samples           │
│  ├── users/{user_id}/avatar/  — encrypted avatar video            │
│  └── users/{user_id}/exports/ — data export ZIPs                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 4. Async Processing (Redis + Celery)

All long-running tasks are offloaded to Celery workers:

```python
# Task definitions
@celery_app.task(queue="twin_engine")
def process_incoming_message(incoming_message_id: str): ...

@celery_app.task(queue="ingestion")
def ingest_instagram_content(user_id: str, access_token: str): ...

@celery_app.task(queue="ingestion")
def ingest_gmail_content(user_id: str): ...

@celery_app.task(queue="identity")
def regenerate_style_vector(user_id: str): ...

@celery_app.task(queue="identity")
def run_weekly_calibration(user_id: str): ...

@celery_app.task(queue="voice")
def create_voice_clone(user_id: str, recording_s3_key: str): ...

@celery_app.task(queue="avatar")
def create_avatar_clone(user_id: str, video_s3_key: str): ...

@celery_app.task(queue="cleanup")
def delete_expired_raw_biometric_data(): ...
```

**Queue priorities:**

| Queue | Workers | Priority | Purpose |
|---|---|---|---|
| twin_engine | 4 | High | Draft generation (latency-sensitive) |
| ingestion | 2 | Medium | Content ingestion at onboarding |
| identity | 1 | Low | Background profile updates |
| voice / avatar | 1 each | Low | Biometric model creation |
| cleanup | 1 | Lowest | Scheduled data deletion |

---

### 5. Web App (Next.js — Vercel)

The web app is the browser-based version of the mobile approval interface. Built with Next.js, deployed on Vercel (free tier), connects to the FastAPI backend via REST + WebSocket.

**Key pages:**

| Page | Purpose |
|---|---|
| `/dashboard` | Pending drafts, twin activity feed, approval rate |
| `/drafts/{id}` | Full draft review — approve / edit / reject |
| `/identity` | View and edit twin profile, vocabulary, topics |
| `/channels` | Connect/disconnect Instagram, Gmail, etc. |
| `/settings` | Model selection (BYOK), voice/avatar provider, autonomy settings |
| `/audit` | Full audit log of all twin actions |
| `/privacy` | Consent management, data export, account deletion |

**Tech:**
- Framework: Next.js 15 (App Router)
- Hosting: Vercel (free tier — auto-deploy from GitHub)
- Auth: JWT from FastAPI backend (same tokens as mobile)
- Real-time: WebSocket connection for live draft notifications
- Styling: Tailwind CSS

---

### 6. Landing Page (Next.js — Vercel)

Marketing site at `selph.ai`. Separate Next.js project on Vercel.

**Key sections:**
- Hero — "Your Digital Self" + waitlist CTA
- How it works — 3-step explainer (capture → twin → approve)
- Features — voice, avatar, mind clone, multi-model
- Pricing — Free / Creator / Pro / Executive / Enterprise tiers
- Trust & Safety — SELPH SAFE framework, EU AI Act compliance
- "Start for free" → redirects to Web App signup

**Tech:**
- Framework: Next.js 15 (static export)
- Hosting: Vercel (free tier)
- Domain: `selph.ai` via Cloudflare DNS → Vercel

---

### 7. Mobile App (React Native)

**Key screens and their API dependencies:**

| Screen | Key API Calls |
|---|---|
| Onboarding — Consent | `POST /consent` |
| Onboarding — Profile Setup | `POST /identity/profile`, `POST /identity/topics` |
| Onboarding — Connect Channels | `GET /channels/instagram/auth`, `GET /channels/gmail/auth` |
| Home / Dashboard | `GET /drafts/pending`, `GET /identity/confidence` |
| Draft Review | `GET /drafts/{draft_id}`, `POST /drafts/{draft_id}/approve`, `POST /drafts/{draft_id}/edit`, `POST /drafts/{draft_id}/reject` |
| Twin Profile | `GET /identity/profile`, `PATCH /identity/profile` |
| Settings — Data & Privacy | `GET /consent`, `DELETE /account`, `GET /account/export` |

---

### 6. External API Integrations

```
┌──────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                       │
│                                                          │
│  LiteLLM Gateway (multi-model router)                    │
│  ├── claude-sonnet-4-6 (Anthropic) — default            │
│  ├── gpt-5 (OpenAI) — user-selectable                   │
│  ├── gemini-2.0 (Google) — user-selectable              │
│  ├── deepseek-chat (DeepSeek) — user-selectable         │
│  ├── mistral-large (Mistral) — user-selectable          │
│  └── ollama/* (local) — zero API cost option            │
│                                                          │
│  Voyage AI                                               │
│  └── voyage-3 — all embeddings (identity + semantic)    │
│                                                          │
│  Voice Clone (pluggable)                                 │
│  ├── Chatterbox — default (MIT, free, self-hosted)      │
│  └── ElevenLabs — optional premium (user BYOK)          │
│                                                          │
│  Avatar Clone (pluggable)                                │
│  ├── Linly-Talker — default (MIT, free, self-hosted)    │
│  ├── Duix-Avatar — alternative open-source              │
│  └── HeyGen — optional premium (user BYOK)              │
│                                                          │
│  Firebase (Google)                                       │
│  └── FCM — push notifications to mobile app            │
│                                                          │
│  Meta Graph API                                          │
│  └── Instagram DM webhooks + message send               │
│                                                          │
│  Google APIs                                             │
│  ├── Gmail API — email read + send                      │
│  └── Pub/Sub — Gmail push notification trigger          │
│                                                          │
│  Cloudflare R2                                           │
│  └── encrypted biometric file storage (S3-compatible)  │
│                                                          │
│  Resend                                                  │
│  └── transactional email (deletion certs, etc.)        │
└──────────────────────────────────────────────────────────┘
```

---

## Request Flow: Message → Draft → Approval → Send

```
1. MESSAGE ARRIVES
   Instagram webhook → POST /webhooks/instagram
   Channel Adapter normalizes → IncomingMessage
   Celery task queued: process_incoming_message(message_id)

2. TWIN ENGINE RUNS (async, ~5-8 seconds total)
   load_context        → PostgreSQL + pgvector queries (~0.5s)
   route_channel       → apply CHANNEL_CONSTRAINTS (~0ms)
   build_prompt        → dynamic system + user prompt (~0ms)
   generate_draft      → Claude API call (~3-5s)
   score_confidence    → embedding + cosine sim (~0.5s)
   moderate            → safety checks (~0.1s)
   route_approval      → store draft, interrupt graph (~0ms)

3. PUSH NOTIFICATION SENT
   Firebase FCM → iOS/Android device
   Notification: "{Sender} messaged you — twin drafted a reply"

4. USER REVIEWS IN APP
   GET /drafts/{draft_id} → load draft + confidence + original message
   User taps: Approve / Edit / Reject / Skip

5. DECISION PROCESSED
   POST /drafts/{draft_id}/approve
   Backend resumes LangGraph graph (interrupt resolved)
   process_decision_node runs:
     → send_message() via channel API
     → update_identity_from_feedback()
     → log_audit()

6. MESSAGE SENT
   Instagram API / Gmail API / etc. → message delivered to sender
   App shows: "Sent ✓"
```

---

## Deployment Architecture

```
┌──────────────────────────────────┐  ┌──────────────────────────────┐
│         Vercel (frontend)        │  │       Railway (backend)       │
│                                  │  │                               │
│  selph.ai (Landing Page)         │  │  FastAPI App    (Docker)      │
│  ├── Next.js static site         │  │  Celery Workers (Docker)      │
│  ├── Waitlist / Pricing          │  │  Celery Scheduler (Docker)    │
│  └── "Start free" → web app      │  │  Chatterbox     (Docker)      │
│                                  │  │  Linly-Talker   (Docker)      │
│  app.selph.ai (Web App)          │  │                               │
│  ├── Next.js App Router          │  │  PostgreSQL + pgvector (mgd)  │
│  ├── Draft approval dashboard    │  │  Redis              (mgd)     │
│  ├── Twin profile management     │  │                               │
│  ├── REST API ← → FastAPI        │  │  Railway built-in proxy       │
│  └── WebSocket ← → FastAPI       │  │  (auto TLS)                   │
└──────────────────────────────────┘  └──────────────────────────────┘
                    │                               │
                    └──────────┬────────────────────┘
                               │
              ┌────────────────┴────────────────────┐
              │         Cloudflare (free)            │
              │  DNS → selph.ai + app.selph.ai       │
              │  WAF → DDoS + rate limiting          │
              │  R2  → voice / avatar / export files │
              └─────────────────────────────────────┘

React Native App (iOS / Android)
  ├── Same REST API as Web App
  ├── Firebase FCM → push notifications
  └── App Store / Google Play
```

**Scaling triggers:**

| Service | Scale-Out Trigger | Action |
|---|---|---|
| FastAPI | CPU > 70% or p95 latency > 2s | Scale Railway service replicas |
| Celery twin_engine | Queue depth > 10 | Add worker replicas |
| Celery ingestion | Queue depth > 5 | Add worker replicas |
| PostgreSQL | 1K+ active users | Upgrade Railway plan |

---

## Security Architecture

```
Transport:   All traffic TLS 1.3 (Railway auto-TLS + Cloudflare)
API Auth:    JWT (RS256) — 15-min access token, 7-day refresh token
Webhooks:    HMAC-SHA256 signature verification on all incoming webhooks
Storage:     AES-256 encryption at rest (application-layer, libsodium)
Biometrics:  User-specific encryption key per user for voice/avatar files
Network:     Railway private networking for DB + Redis (no public access)
Secrets:     Railway environment variables (encrypted at rest)
WAF:         Cloudflare WAF (OWASP top 10 rules + rate limiting, free tier)
```

---

## Environment Configuration

```
Development:   Local Docker Compose (Postgres + Redis containers)
Staging:       Railway (staging environment, real external APIs, feature-flagged)
Production:    Railway (production environment, auto-scaling, full monitoring)

Feature flags: All external API calls (Chatterbox, Linly-Talker, ElevenLabs optional, HeyGen optional, Instagram) gated
               behind feature flags in staging to prevent accidental production calls
```

---

*Status: System Architecture v1.0 — Covers all 8 build phases*
