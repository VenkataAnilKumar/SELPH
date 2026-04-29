<div align="center">

```
███████╗███████╗██╗     ██████╗ ██╗  ██╗
██╔════╝██╔════╝██║     ██╔══██╗██║  ██║
███████╗█████╗  ██║     ██████╔╝███████║
╚════██║██╔══╝  ██║     ██╔═══╝ ██╔══██║
███████║███████╗███████╗██║     ██║  ██║
╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝
```

# Your Digital Self

**The AI that doesn't just help you — it becomes you.**

[![Build](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](.)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey?style=flat-square)](.)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20LangGraph%20%7C%20pgvector-orange?style=flat-square)](docs/05-technical/SELPH_System-Architecture.md)
[![LLMs](https://img.shields.io/badge/LLMs-140%2B%20via%20LiteLLM-red?style=flat-square)](.)

> *"In the future, everyone will have a digital twin. Not a chatbot. Not an assistant. A second self."*

**[See the Demo →](DEMO.md)** · **[Architecture](docs/05-technical/SELPH_System-Architecture.md)** · **[API Docs](docs/05-technical/SELPH_API-Design.md)**

</div>

---

## What is SELPH?

SELPH is a **universal Digital Twin AI** that learns your communication style, voice, avatar, expertise, and topic boundaries — then drafts responses on your behalf across any channel, with **you always in the loop**.

It is not a chatbot. It is not an assistant. It **is you** — available 24/7.

```
Fan sends a DM at 3 AM
        ↓
SELPH loads your identity model (voice, style, topics, briefings, sender tier)
        ↓
Drafts a reply that sounds exactly like you — warm, casual, on-brand
        ↓
Sends you a push notification: "Draft ready. 92% confidence."
        ↓
You tap Approve in 2 seconds. Done.
        ↓
Your fan thinks you wrote it. You kind of did — your twin did.
        ↓
SELPH logs the approval. Updates your model. Gets better.
```

---

## The Problem Everyone Has

| Who | The Pain |
|---|---|
| Content Creators | 50,000 DMs. No time. Fans feel ignored. |
| Consultants | Repeating the same answer 20 times a day. Slow replies = lost deals. |
| Developers | Buried in GitHub issues, code review requests, Slack threads. |
| Executives | Drowning in email. Every reply burns decision energy. |
| Everyone | Wishing they could be in two places at once. |

Generic AI assistants complete tasks. **SELPH represents you.**

---

## How It Works

### Your Identity — Four Layers

```
┌─────────────────────────────────────────────────────────┐
│                   YOUR IDENTITY                          │
│                                                          │
│  Voice Clone    →  Sounds like you (accent, pace, warmth)│
│  Avatar Clone   →  Looks like you (face, expressions)   │
│  Mind Clone     →  Thinks like you (style, expertise)   │
│  Data Layer     →  Knows your context (topics, history) │
└─────────────────────────────────────────────────────────┘
```

### The Twin Engine

```
Incoming message
      │
      ▼
  Context Loader
  ├─ Your identity profile + semantic embeddings
  ├─ Active Twin Briefings ("I'm at a conference this week")
  ├─ Sender Tier (VIP → bypass twin / Priority → always review)
  └─ Recent conversation history
      │
      ▼
  Prompt Builder  →  Draft Generator (LangGraph + LiteLLM)
                          │
                    Confidence Scorer
                          │
              ┌───────────┴──────────────┐
           Low confidence             High confidence
           Full review required       Quick-approve flow
                          │
                  Content Moderator (always on)
                          │
                  Push Notification → Your phone
                          │
                  You: Approve / Edit / Reject
                          │
                  Twin logs decision → Learns → Gets better
```

### Two Modes for Every Situation

| Transparent Mode | Private Mode |
|---|---|
| "Hi, I'm [Name]'s SELPH Digital Twin" | Twin drafts invisibly. You review and send. |
| Honest. Builds trust. Status symbol. | Seamless. No one knows. Your words, your name. |
| Best for creators, public figures | Best for consultants, executives |

Both modes are selectable per conversation or per channel.

---

## What's Been Built

> This is a working product — not a prototype. Every feature below is implemented, tested, and shipped.

**Identity & Onboarding**
- Twin profile with domain, tone, vocabulary, and communication style
- Topic expertise model — twin knows what you know and how confident you are
- Identity verification and consent architecture per channel and feature
- Onboarding status tracking and iterative profile refinement

**Twin Engine**
- Context loading with semantic search across your identity profile
- Channel-aware prompt building (Instagram vs Gmail behave differently)
- Confidence scoring on every draft — low confidence always escalates to you
- Content moderation on all outputs, always on

**Human-in-the-Loop Approval**
- Approve, edit, or reject any draft in one tap
- Rejection reasons feed back into the twin — it learns what you don't sound like
- Push notifications with draft previews
- Emergency pause from the home screen

**Voice & Avatar**
- Voice clone using Chatterbox (MIT, free by default) or ElevenLabs (paid optional)
- Avatar generation using open-source providers (free default) or HeyGen (paid optional)
- Consent and enrollment flow for both; assets stored in encrypted cloud storage

**Advanced Features**
- **Twin Briefing** — inject real-time context into every draft (conference week, availability, opinions)
- **VIP Sender Tiers** — route your most important people directly to you, bypassing the twin
- **Batch Pattern Approval** — cluster similar messages, approve 50 personalized replies in one tap
- **Batch Personalization** — each approved batch reply is uniquely tailored per sender

**Channels (Live)**
- Instagram DMs — OAuth + webhook pipeline
- Gmail — OAuth + push subscription pipeline

**Analytics & Quality**
- Approval rate tracking (your north star metric)
- Weekly digest — messages handled, time saved, top topics
- Performance summary and quality trend over time
- Creator referral program

---

## Three Features No One Else Has

### 1. Twin Briefing — Real-Time Context Injection

Tell your twin something that matters right now. Every draft reflects it until it expires.

```json
POST /v1/identity/briefings
{
  "type": "availability",
  "content": "I'm at a conference this week. Keep replies brief and offer a call next week.",
  "expires_at": "2026-05-05T00:00:00Z"
}
```

Briefing types: `fact` · `opinion` · `instruction` · `availability` · `boundary`

No prompt engineering. No remembering to add context. Your twin just knows.

---

### 2. VIP Sender Tiers — Your Twin Knows Who Matters

```
Tier 0  VIP      →  Routes straight to you. Twin never sees it.
Tier 1  Priority →  Twin drafts, but you always review — no auto-send ever.
Tier 2  Standard →  Normal twin flow. Approve in one tap.
Tier 3  Cold     →  Twin filters and handles; minimal attention needed.
```

Your closest relationships bypass the twin entirely. The twin suggests tier upgrades as trust builds.

---

### 3. Batch Pattern Approval — 50 Replies in One Tap

```
50 fans ask the same question this week
        ↓
SELPH clusters them semantically
        ↓
Generates 1 template + 50 personalized replies
        ↓
You see: "47 similar messages. Preview → Approve All"
        ↓
Tap. Done. 47 people get personal replies. 4 seconds of your time.
        ↓
Per-sender exclusions available. Full audit log per batch.
```

No other digital twin product solves creator-scale approval fatigue.

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI                                                                  │
│  140+ LLM providers via LiteLLM — BYOK, cost tracking, fallback     │
│  Default: claude-sonnet-4-6 | Also: GPT-5, Gemini, DeepSeek,       │
│           local models via Ollama (zero API cost), Mistral          │
│  Orchestration: LangGraph (human-in-the-loop, interruptible)        │
│  Voice: open-source MIT default / ElevenLabs paid optional          │
│  Avatar: open-source MIT default / HeyGen paid optional             │
├─────────────────────────────────────────────────────────────────────┤
│  Backend                                                             │
│  Python + FastAPI · async task queue · PostgreSQL + pgvector        │
│  Semantic identity search · encrypted asset storage · WebSocket     │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend                                                            │
│  Web dashboard: Next.js 15 (App Router)                             │
│  Mobile: React Native (iOS + Android)                               │
├─────────────────────────────────────────────────────────────────────┤
│  Channels                                                            │
│  Instagram DMs · Gmail · (Twitter/X, WhatsApp, Slack, GitHub next) │
├─────────────────────────────────────────────────────────────────────┤
│  Compliance                                                          │
│  C2PA watermarking · E2E encryption · GDPR · CCPA                  │
│  EU AI Act · India IT Rules · SOC 2 audit in progress              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/VenkataAnilKumar/selph.git
cd selph

# Configure
cp .env.example .env
# Add your LLM API key (Anthropic, OpenAI, or any LiteLLM-supported provider)

# Start
docker compose up --build

# API → http://localhost:8000
# Interactive docs → http://localhost:8000/docs
```

**End-to-end demo with curl commands → [DEMO.md](DEMO.md)**

---

## Project Structure

```
selph/
├── src/
│   ├── backend/app/
│   │   ├── routers/    auth, twin, drafts, messages, channels, identity, referrals
│   │   ├── services/   twin_engine, draft, identity, moderation, twin_learning
│   │   ├── models/     user, twin, message, draft, identity_profile, briefing,
│   │   │               sender_tier, message_cluster, batch_send, audit_log, consent
│   │   ├── channels/   gmail, instagram (OAuth + webhook adapters)
│   │   ├── voice/      provider registry (open-source + paid options)
│   │   ├── avatar/     provider registry (open-source + paid options)
│   │   └── tasks/      draft generation, voice synthesis, avatar generation, push notifications
│   ├── web/            Next.js dashboard
│   └── mobile/         React Native app (iOS + Android)
├── docs/
│   ├── 01-product/     product vision, PRD
│   ├── 02-market/      market validation, feature expansion research
│   ├── 03-specs/       twin engine, identity model, feature specs
│   ├── 04-safety/      risk, privacy consent, policy matrix
│   └── 05-technical/   system architecture, database schema, API design
├── docker-compose.yml  One command local setup
└── DEMO.md             Live API walkthrough
```

---

## Running Tests

```bash
# Backend
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v

# Web
cd src/web && npm install && npm run test

# Mobile
cd src/mobile && npm install && npm run test
```

---

## Business Model

| Tier | Price | Who | What |
|---|---|---|---|
| **Free** | $0/mo | Everyone | 50 interactions/month, text twin |
| **Creator** | $39/mo | Influencers | Voice + avatar, 500 interactions, social channels |
| **Pro** | $99/mo | Consultants, Devs | Unlimited interactions, all channels, private mode |
| **Executive** | $299/mo | Leaders | Priority processing, advanced analytics, enterprise security |
| **Enterprise** | Custom | Companies | Per-seat, SSO, compliance, dedicated SLA |

**North Star Metric:** Twin Approval Rate — the percentage of drafts approved without edits.
Higher = your twin sounds more like you = better product = deeper moat.

---

## Why SELPH Wins

| Generic AI Agent | SELPH |
|---|---|
| Completes tasks | Completes tasks **as you** |
| Speaks as "AI" | Speaks in **your voice** |
| No personality | **Your personality** |
| Same output for everyone | **Unique to every user** |
| No trust model | **Graduated trust — earned over time** |
| Fragmented point solutions | **Unified identity twin** |
| Reactive only | **Proactive — surfaces what you'd miss** |
| Breaks at creator scale | **Batch Pattern Approval — 50 replies in one tap** |

---

## Safety & Ethics

SELPH is built trust-first, not growth-first.

- **Always transparent** — recipients can verify any twin interaction via cryptographic link
- **C2PA watermarking** on all twin-generated content — traceable forever
- **Hard limits by default** — financial, legal, medical actions always blocked
- **Anomaly detection** — auto-pause if twin behavior deviates from baseline
- **Full audit log** — every twin action logged immutably
- **Consent architecture** — explicit consent required per channel, per feature
- **Compliant from day 1** — GDPR, CCPA, EU AI Act, India IT Rules
- **VIP bypass** — your most important relationships never touch the twin

Policy decisions: [SELPH_Canonical-Policy-Matrix.md](docs/04-safety/SELPH_Canonical-Policy-Matrix.md)

---

## Key Documents

| Document | What It Contains |
|---|---|
| [Product Vision](docs/01-product/PRODUCT_IDEA.md) | The idea, identity layers, operating modes |
| [PRD](docs/01-product/PRD.md) | Goals, user stories, full feature list, business model |
| [System Architecture](docs/05-technical/SELPH_System-Architecture.md) | Full stack design, data flows, deployment |
| [Database Schema](docs/05-technical/SELPH_Database-Schema.md) | All tables, relationships, vector design |
| [API Design](docs/05-technical/SELPH_API-Design.md) | Every endpoint, request/response shapes |
| [Twin Engine Spec](docs/03-specs/SELPH_Twin-Engine-Spec.md) | Pipeline design, confidence scoring, moderation |
| [Feature Expansion Spec](docs/03-specs/SELPH_Feature-Expansion-Spec.md) | Briefing, VIP tiers, batch approval, proactive twin |
| [Safety Policy Matrix](docs/04-safety/SELPH_Canonical-Policy-Matrix.md) | Canonical policy decisions, enforcement rules |

---

## Contributing

1. Branch: `git checkout -b feature/your-feature`
2. Write tests alongside code
3. Commit: `git commit -m "feat: add thing"`
4. Push and open a PR — CI must pass
5. Get approval and merge

---

<div align="center">

## Be everywhere. Be SELPH.

**[Full Demo Walkthrough →](DEMO.md)**

---

*SELPH — **S**elf · **E**cho · **L**ive · **P**roxy · **H**uman*

</div>
