# SELPH — Full Project Context

> **Purpose:** Load this file at the start of any new conversation to instantly restore full project context.
> **Last updated:** 2026-04-27
> **Status:** Implementation Plan complete — ready to write Phase 0 code

---

## 1. What Is SELPH

SELPH is a **Universal Digital Twin AI** that learns who you are — your voice, avatar, expertise, and communication style — and acts on your behalf across any platform, for any person, in any domain.

**Tagline:** *"Your Digital Self"*
**Domain:** selph.ai

Unlike generic AI assistants, SELPH **becomes you** — a living digital version that thinks, responds, and creates the way you would, with human-in-the-loop approval on every action.

```
Your Device + Your Data + Your Voice + Your Avatar
                      ↓
                 SELPH Twin
                      ↓
       Analyzes incoming messages/tasks
                      ↓
       Drafts responses AS YOU
                      ↓
       Notifies you → You approve / edit / reject
                      ↓
       SELPH learns from every decision
```

---

## 2. Identity Layers

| Layer | What It Captures | Technology |
|---|---|---|
| **Voice Clone** | Tone, accent, speech patterns | Chatterbox (MIT, default) / ElevenLabs (paid, optional) |
| **Avatar Clone** | Face, expressions, visual presence | Linly-Talker (MIT, default) / HeyGen (paid, optional) |
| **Mind Clone** | Expertise, decisions, communication style | LiteLLM + pgvector identity profiles |
| **Data Layer** | Device, files, messages, work history | PostgreSQL + Cloudflare R2 |

---

## 3. Target Users (Wave Order)

1. **Content Creators** — fan engagement, DM replies, comment responses (MVP target)
2. **Consultants & Freelancers** — client intake, proposals, FAQ handling
3. **Developers** — GitHub issues, code reviews, technical emails
4. **Executives** — email drafting, meeting briefs, decision filtering
5. **General Public** — universal twin for everyone

---

## 4. Operating Modes

**Transparent Mode (default):**
> "Hi, I'm [Name]'s SELPH — their Digital Twin. They'll review my response before it reaches you."

**Private Mode:**
> Twin drafts everything. You review and send. Recipient never knows.

---

## 5. Tech Stack — All Decisions Locked

| Component | Technology | Notes |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async, AI-friendly |
| Database | PostgreSQL 16 + pgvector | Railway managed — NO external vector DB |
| Vector Search | pgvector (co-located) | Replaces Pinecone entirely |
| Cache / Queue broker | Redis | Railway managed |
| Task Queue | Celery | 4 queues: drafts, channels, voice, avatar |
| LLM Gateway | LiteLLM | 140+ models, BYOK, default: claude-sonnet-4-6 |
| Local LLM | Ollama | Zero API cost option |
| Voice Clone | Chatterbox (MIT, free, default) | ElevenLabs = optional paid premium |
| Avatar Clone | Linly-Talker / Duix-Avatar (MIT, free, default) | HeyGen = optional paid premium |
| Auth | JWT RS256 | Shared: mobile + web + landing |
| Web App | Next.js 15 (App Router) | app.selph.ai — Vercel |
| Landing Page | Next.js 15 (static export) | selph.ai — Vercel |
| Mobile App | React Native (Expo) | iOS + Android |
| Shared Package | @selph/shared (npm workspace) | API client, types, constants |
| Object Storage | Cloudflare R2 | S3-compatible, free 10GB, zero egress |
| DNS / WAF | Cloudflare | Free TLS, DDoS protection |
| Backend Hosting | Railway | Docker + managed PostgreSQL + Redis |
| Frontend Hosting | Vercel | Free tier, auto-deploy from GitHub |
| Push Notifications | Firebase FCM | Mobile + web push |
| Email | Resend | Transactional email |
| Encryption | libsodium | App-level, replaces AWS KMS |
| Observability | Railway logs + Sentry | No AWS CloudWatch |

### What We Are NOT Using
- ❌ AWS (ECS, S3, KMS, SES, Route 53, CloudFront, WAF) — replaced entirely
- ❌ Pinecone — replaced by pgvector on Railway PostgreSQL
- ❌ Kafka — replaced by Celery + Redis for MVP
- ❌ ClickHouse — replaced by audit_logs table in PostgreSQL
- ❌ ElevenLabs as default — it is optional paid premium only
- ❌ HeyGen as default — it is optional paid premium only

---

## 6. Repo Structure (Final — Validated 2026-04-27)

```
selph-ai/                           ← GitHub repo (private)
│
├── docs/                           ← All documentation (this folder)
│   ├── 01-product/
│   ├── 02-market/
│   ├── 03-specs/
│   ├── 04-safety/
│   ├── 05-technical/
│   ├── 06-implementation/
│   └── 07-design/
│
├── src/                            ← All source code
│   ├── backend/                    ← FastAPI — Railway
│   │   ├── app/                    ← Python package (imports: from app.x)
│   │   │   ├── main.py             ← Entry point, /v1/ prefix on all routes
│   │   │   ├── config.py           ← Settings + feature flags
│   │   │   ├── database.py         ← SQLAlchemy engine + session
│   │   │   ├── models/             ← ORM models (table ownership map)
│   │   │   ├── schemas/            ← Pydantic request/response models
│   │   │   ├── routers/            ← /v1/auth, /v1/twin, /v1/drafts, /v1/messages, /v1/channels
│   │   │   ├── channels/           ← Channel adapter pattern (base, instagram, gmail, registry)
│   │   │   ├── services/           ← Business logic + service registry (microservice boundaries)
│   │   │   ├── workers/            ← Celery tasks (draft, channel, voice, avatar)
│   │   │   └── middleware/         ← JWT RS256 auth
│   │   ├── migrations/             ← Alembic (outside app/, not in Docker image)
│   │   ├── tests/                  ← pytest (outside app/, not in Docker image)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml      ← Local dev: API + worker + postgres + redis
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   └── .env.example
│   │
│   ├── web/                        ← Next.js 15 — app.selph.ai (Vercel)
│   │   ├── app/                    ← Dashboard only (auth guard)
│   │   ├── components/             ← ui/, twin/, layout/
│   │   ├── lib/                    ← auth.ts (token + route guard)
│   │   ├── public/
│   │   ├── tailwind.config.ts
│   │   ├── next.config.ts
│   │   └── package.json
│   │
│   ├── landing/                    ← Next.js 15 static — selph.ai (Vercel)
│   │   ├── app/                    ← Marketing pages + /verify/[id]
│   │   ├── components/             ← Hero, Features, Pricing, HowItWorks
│   │   ├── next.config.ts          ← output: 'export'
│   │   └── package.json
│   │
│   ├── mobile/                     ← React Native Expo — iOS + Android
│   │   ├── app/                    ← Expo Router
│   │   ├── components/             ← DraftCard (swipe gesture), TwinStatusBanner
│   │   ├── lib/                    ← notifications.ts
│   │   ├── app.json
│   │   └── package.json
│   │
│   ├── shared/                     ← @selph/shared npm workspace
│   │   ├── api/                    ← client.ts, auth.ts, twin.ts, drafts.ts, channels.ts
│   │   ├── types/                  ← twin.ts, auth.ts, channel.ts
│   │   ├── constants/              ← CHANNEL_COLORS, CONFIDENCE_THRESHOLDS
│   │   └── package.json            ← name: "@selph/shared"
│   │
│   └── services/                   ← Future microservice stubs (empty now)
│       ├── twin-engine/            ← Extract Phase 3
│       ├── identity/               ← Extract Phase 3
│       ├── voice/                  ← GPU worker Phase 6
│       └── avatar/                 ← GPU worker Phase 7
│
├── package.json                    ← npm workspaces root
└── README.md
```

---

## 7. Database — Table Ownership Map

| Table | Owned By | Key Columns |
|---|---|---|
| `users` | Auth | id, email, name, password_hash |
| `twins` | Twin Engine | user_id, is_active, mode |
| `identity_profiles` | Identity | user_id, tone, vocabulary, sample_responses, voice_model_id, avatar_model_id |
| `identity_samples` | Identity | profile_id, embedding Vector(1536), channel, incoming, response |
| `messages` | Channel | twin_id, channel, sender_id, content, status |
| `drafts` | Twin Engine | message_id, content, confidence, confidence_label, status |
| `audit_logs` | Audit | twin_id, action, hashed fields, user_action, twin_version |

**pgvector:** `CREATE EXTENSION IF NOT EXISTS vector;` — run in first migration.

---

## 8. Key API Patterns

```
All routes: /v1/<resource>/*

POST /v1/auth/signup          → creates user + twin record
POST /v1/auth/login           → returns JWT RS256 token
GET  /v1/twin/me              → twin status + mode
POST /v1/twin/pause           → pause twin
POST /v1/twin/resume          → resume twin
GET  /v1/drafts/pending       → list pending approvals
POST /v1/drafts/:id/action    → approve | edit | reject | skip
POST /v1/channels/:ch/connect → OAuth connect channel
GET  /health                  → {status, service, db, redis, version}
```

---

## 9. Key Code Patterns

### Channel Adapter (never hardcode channel names)
```python
# app/channels/registry.py
adapter = get_adapter("instagram_dm")  # returns InstagramAdapter
message = adapter.parse_incoming(raw_payload)
adapter.send_reply(sender_id, content, credentials)
```

### Service Registry (microservice extraction boundary)
```python
# Always call through registry, never import services directly
from app.services.registry import services
profile = services.identity.get_profile(user_id)
draft   = services.twin_engine.run_pipeline(message, profile)
```

### Twin Engine Boundary
```python
# Celery calls run_twin_pipeline() — not generate_draft() directly
# MVP: LiteLLM call. Phase 3: LangGraph. Phase 4: HTTP service.
def run_twin_pipeline(message, profile) -> str:
    return generate_draft(message, profile)
```

### Confidence Scoring Thresholds
```python
HIGH_CONFIDENCE   = 0.85+  → "Ready to send"
MEDIUM_CONFIDENCE = 0.65+  → "Review suggested"
LOW_CONFIDENCE    = <0.65  → "Needs your input"
```

### Feature Flags (Railway env vars, all False by default)
```python
FEATURE_VOICE_CLONE, FEATURE_AVATAR_CLONE
FEATURE_BATCH_APPROVAL, FEATURE_TWIN_BRIEFING, FEATURE_VIP_OVERRIDE
FEATURE_INSTAGRAM_DM, FEATURE_GMAIL
```

---

## 10. MVP Build Phases

| Phase | Goal | Duration | Done When |
|---|---|---|---|
| **0** | Foundation — auth, DB, base API, docker | Week 1–2 | /health 200, signup works, DB running |
| **1** | Identity Core — onboarding, social ingestion, profile | Week 2–4 | Profile built, visible in app |
| **2** | Twin Engine — draft generation, confidence | Week 4–6 | Twin drafts text responses |
| **3** | Approval Loop — push notification, approve/edit/reject | Week 6–7 | One-tap approve works |
| **4** | Safety Layer — moderation, watermark, audit | Week 7–8 | All drafts moderated before delivery |
| **5** | Channels — Instagram DM + Gmail (Pub/Sub push) | Week 8–10 | Real messages processed |
| **6** | Voice Clone — Chatterbox default | Week 10–12 | Voice sounds like user |
| **7** | Avatar Clone — Linly-Talker default | Week 12–14 | Video avatar works |
| **8** | Beta Launch — 50 creators | Week 14–16 | NPS > 50 |

**Minimum Viable Demo:** Phases 0–3 (6 weeks)

---

## 11. Day-by-Day Build Sequence (Phase 0)

```
Day 1   Repo setup, Docker, postgres + redis running locally
Day 2   All DB models + Alembic migration + pgvector extension
Day 3   Auth — signup, login, JWT RS256
Day 4   Channel adapters (base + registry + Instagram + Gmail stubs)
Day 5   Celery app (4 queues) + voice/avatar task placeholders
Day 6   Service registry + run_twin_pipeline() boundary
Day 7   LiteLLM + draft generation (hardcoded profile test)
Day 8   Confidence scoring + moderation + draft/twin routes (/v1/)
Day 9   Identity profile model + onboarding questionnaire API
Day 10  Next.js setup + design tokens + API client (@selph/shared)
Day 11  Dashboard page + DraftCard component (web)
Day 12  Expo mobile setup + home screen + DraftCard native
Day 13  Railway deploy (API + worker) + Vercel deploy (web + landing)
Day 14  Firebase push + end-to-end test: message → draft → notify → approve
```

---

## 12. UI/UX Design System — v3.0 Light & Colorful 2026

**Manifesto:** "Your second self — bright, alive, and unmistakably you."

### Colors
```
Canvas:   #FFFFFF (white), #FAFAF9 (warm white), #F5F3FF (cloud), #F0F9FF (mist)
Brand:    #7C3AED (violet), #9333EA (purple), #0EA5E9 (sky), #F43F5E (coral),
          #F97316 (orange/tangerine), #10B981 (emerald)
Text:     #0F172A (title), #334155 (body), #64748B (muted), #94A3B8 (subtle)
Semantic: #10B981 (approve), #F59E0B (edit), #EF4444 (reject), #F97316 (flag)
```

### Key Gradients
```css
Primary:  linear-gradient(135deg, #7C3AED, #0EA5E9)   /* violet → sky */
Energy:   linear-gradient(135deg, #F43F5E, #F97316)   /* coral → orange */
Success:  linear-gradient(135deg, #10B981, #06B6D4)   /* emerald → cyan */
Identity ring: conic-gradient(from 0deg, #7C3AED, #0EA5E9, #10B981, #F43F5E, #7C3AED)
```

### Fonts
- Display: Plus Jakarta Sans (Bold 700/800)
- Body: Inter (Regular 400)
- Code: JetBrains Mono

### Motion
- Spring physics on buttons (`type: 'spring', stiffness: 400, damping: 20`)
- Card entrance: `opacity 0 → 1, y 20 → 0, duration 0.5s`
- Swipe to approve on mobile (Reanimated 3, threshold: 100px)
- Spinning conic gradient ring on identity avatar

### Implementation
- Next.js 15 + Tailwind v4 + Framer Motion 12 + Radix UI + Lucide React
- React Native + NativeWind + Reanimated 3 + Gesture Handler

---

## 13. Safety — SELPH SAFE Framework

| Principle | Implementation |
|---|---|
| **S** — Safe | Content moderation before every draft reaches user |
| **A** — Accountable | Full audit log, every action hashed and timestamped |
| **F** — Fair | No financial/legal/medical advice, no discrimination |
| **E** — Ethical | Transparent mode default, AI labeling, watermarking |

- All text outputs: invisible Unicode watermark
- Human-in-the-loop: NEVER fully autonomous without permission
- Anomaly detection: pause twin + alert if approval rate drops < 40%
- Data retention: user controls, right to erasure, GDPR compliant

---

## 14. Microservice Strategy

**Now (MVP):** Modular monolith — everything in `src/backend/`

**Extraction triggers (when to split):**
- Voice/Avatar → when Phase 6/7 launches (GPU needed)
- Identity → when pgvector queries > 100ms p95
- Twin Engine → when LLM calls queue up behind each other

**Extraction is painless because:**
- Each `app/services/<name>.py` maps to a future service
- Channel adapters already isolated
- Service registry means only `registry.py` changes (local call → HTTP call)
- Celery queues already split (drafts, channels, voice, avatar)

---

## 15. Document Index

All 19 documents validated and stale-reference-free as of 2026-04-27:

| # | File | Status |
|---|---|---|
| 1 | `01-product/PRODUCT_IDEA.md` | ✅ Clean |
| 2 | `01-product/PRD.md` | ✅ Clean |
| 3 | `02-market/VALIDATION.md` | ✅ Clean |
| 4 | `02-market/FEATURE_VALIDATION_AND_EXPANSION.md` | ✅ Clean |
| 5 | `03-specs/SELPH_Twin-Engine-Spec.md` | ✅ Clean |
| 6 | `03-specs/SELPH_Identity-Model-Spec.md` | ✅ Clean |
| 7 | `03-specs/SELPH_Feature-Expansion-Spec.md` | ✅ Clean |
| 8 | `04-safety/RISK_MITIGATION.md` | ✅ Clean |
| 9 | `04-safety/SELPH_Canonical-Policy-Matrix.md` | ✅ Clean |
| 10 | `04-safety/SELPH_Privacy-Consent.md` | ✅ Clean |
| 11 | `05-technical/SELPH_System-Architecture.md` | ✅ Clean (v1.1) |
| 12 | `05-technical/SELPH_Database-Schema.md` | ✅ Clean |
| 13 | `05-technical/SELPH_API-Design.md` | ✅ Clean |
| 14 | `06-implementation/MVP_BUILD_PLAN.md` | ✅ Clean |
| 15 | `06-implementation/IMPLEMENTATION_PLAN.md` | ✅ Clean (v1.1) |
| 16 | `06-implementation/SPRINT_PLAN_2_WEEKS.md` | ✅ Clean |
| 17 | `06-implementation/BUILD_READINESS_ACTION_PLAN.md` | ✅ Clean |
| 18 | `06-implementation/BUILD_READINESS_SCORECARD.md` | ✅ Clean |
| 19 | `06-implementation/INVESTOR_ONE_PAGER.md` | ✅ Clean |
| 20 | `06-implementation/REFERENCES.md` | ✅ Clean |
| 21 | `07-design/SELPH_UI-UX-Design.md` | ✅ Clean (v3.0) |

**Deleted:** `05-technical/SELPH_Modern-Architecture.md` — replaced by System-Architecture.md (single source of truth)

---

## 16. Where We Left Off

**Last completed:** Implementation Plan v1.1 — repo structure validated and finalized.

**Next action:** Start writing Phase 0 code.

Suggested start order:
1. `src/backend/` — `docker-compose.yml`, DB models, auth, `/health`
2. `src/shared/` — `@selph/shared` package, API client, types
3. `src/web/` — Next.js dashboard, Tailwind tokens, DraftCard
4. `src/landing/` — Next.js marketing site
5. `src/mobile/` — Expo app, home screen, swipe DraftCard

---

*Context file — update after every major session*
*SELPH project root: V:/AI Engineer/Agentic AI and Autonmous AI/SELPH/*
