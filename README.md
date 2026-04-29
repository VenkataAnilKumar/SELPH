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
[![Phases](https://img.shields.io/badge/phases%20shipped-9%2F9-blue?style=flat-square)](.)
[![Readiness](https://img.shields.io/badge/build%20readiness-82%2F100-yellow?style=flat-square)](docs/06-implementation/BUILD_READINESS_SCORECARD.md)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey?style=flat-square)](.)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20LangGraph%20%7C%20pgvector-orange?style=flat-square)](docs/05-technical/SELPH_System-Architecture.md)
[![LLMs](https://img.shields.io/badge/LLMs-140%2B%20via%20LiteLLM-red?style=flat-square)](.)

> *"In the future, everyone will have a digital twin. Not a chatbot. Not an assistant. A second self."*

**[See the Demo →](DEMO.md)** · **[Architecture](docs/05-technical/SELPH_System-Architecture.md)** · **[API Docs](docs/05-technical/SELPH_API-Design.md)** · **[Investor One-Pager](docs/06-implementation/INVESTOR_ONE_PAGER.md)**

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
│  Avatar Clone   →  Looks like you (face, expressions)    │
│  Mind Clone     →  Thinks like you (style, expertise)    │
│  Data Layer     →  Knows your context (files, history)   │
└─────────────────────────────────────────────────────────┘
```

### The Twin Engine Pipeline

```
Incoming message
      │
      ▼
  Context Loader
  ├─ Your identity profile + pgvector embeddings
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

## What Has Been Shipped — All 9 Phases

> This is not a prototype. Every phase is implemented, tested, and merged to main.

| Phase | What Ships |
|---|---|
| **Phase 0** ✅ | Foundation — FastAPI + PostgreSQL + Redis + Celery + JWT auth |
| **Phase 1** ✅ | Identity Core — twin profiles, topic boundaries, onboarding, identity verification |
| **Phase 2** ✅ | Twin Engine — context loading, prompt building, draft generation, confidence scoring |
| **Phase 3** ✅ | Human Loop — approve/edit/reject, push notifications, twin learning from feedback |
| **Phase 4** ✅ | Channels UI — settings, onboarding flow, channel management, mobile dashboard |
| **Phase 5** ✅ | OAuth Ingestion — Instagram DMs + Gmail (OAuth, webhooks, full message pipeline) |
| **Phase 6** ✅ | Voice Clone — Chatterbox (MIT/free) + ElevenLabs (paid optional); consent + enrollment + synthesis |
| **Phase 7** ✅ | Avatar Clone — Linly-Talker/Duix-Avatar (MIT/free) + HeyGen (paid optional); consent + generation |
| **Phase 8** ✅ | Quality & Analytics — approval rates, weekly digest, performance summary, creator referral program |
| **Phase 9** ✅ | Advanced — Twin Briefing, VIP Sender Tiers, Batch Pattern Approval, Batch Personalization render |

**Build Readiness: 82/100** — demo-ready, controlled pilot next.

---

## Three Features No One Else Has

### 1. Twin Briefing — Real-Time Context Injection

Tell your twin something that matters right now. It knows this for every response until it expires.

```python
POST /v1/twin/briefings
{
  "type": "availability",
  "content": "I'm at a conference this week. Keep replies brief and offer a call next week.",
  "expires_at": "2026-05-05T00:00:00Z"
}
# Every draft your twin generates this week will reflect this context.
# No prompt engineering. No remembering to add context. It just knows.
```

Briefing types: `fact` · `opinion` · `instruction` · `availability` · `boundary`
Max 10 active briefings per user. Expiry by date or usage count.

---

### 2. VIP Sender Tiers — Your Twin Knows Who Matters

```
Tier 0  VIP      →  Message routes straight to you. Twin never sees it.
Tier 1  Priority →  Twin drafts, but you always review — no auto-send ever.
Tier 2  Standard →  Normal twin flow. Approve in one tap.
Tier 3  Cold     →  Twin filters and handles; minimal attention needed.
```

Your closest relationships bypass the twin completely. Your twin suggests tier upgrades as trust builds.

---

### 3. Batch Pattern Approval — 50 Replies in One Tap

```
50 fans ask your skincare routine in the same week
        ↓
SELPH clusters them semantically
        ↓
Generates 1 template + 50 personalized replies ("Love your question, @username!")
        ↓
You see: "47 similar messages. Template preview → Approve All"
        ↓
Tap. Done. 47 people get personal replies. You spent 4 seconds.
        ↓
Per-sender exclusions available. Full audit log per batch.
```

No other digital twin product solves creator-scale approval fatigue.

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Layer                                                            │
│  LiteLLM Gateway → 140+ models, BYOK, cost tracking, fallback       │
│  Default: claude-sonnet-4-6 | Also: GPT-5, Gemini, DeepSeek,       │
│           Llama via Ollama (zero cost, local), Mistral              │
│  Orchestration: LangGraph (human-in-the-loop StateGraph)            │
│  Voice: Chatterbox MIT (default, free) / ElevenLabs (paid optional) │
│  Avatar: Linly-Talker/Duix-Avatar MIT (default) / HeyGen (paid)    │
├─────────────────────────────────────────────────────────────────────┤
│  Backend                                                             │
│  FastAPI + Celery on Railway                                         │
│  PostgreSQL + pgvector (identity embeddings + semantic search)       │
│  Redis (identity cache + LangGraph interrupted state)               │
│  Cloudflare R2 (voice + avatar asset storage)                       │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend                                                            │
│  Web App: Next.js 15 on Vercel                                      │
│  Mobile: React Native (iOS + Android)                               │
│  DNS + WAF: Cloudflare                                              │
├─────────────────────────────────────────────────────────────────────┤
│  Channels (live)                                                     │
│  Instagram DMs · Gmail                                               │
│  (Twitter/X, WhatsApp, Slack, GitHub — Phase 2)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Compliance                                                          │
│  C2PA watermarking · E2E encryption · GDPR · CCPA                  │
│  EU AI Act · India IT Rules · SOC 2 path (audit Month 3)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/VenkataAnilKumar/selph.git
cd selph

# 2. Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY (or any LiteLLM-supported key)

# 3. Start
docker compose up --build

# API live at http://localhost:8000
# Interactive API docs at http://localhost:8000/docs
```

**Full demo walkthrough with curl commands → [DEMO.md](DEMO.md)**

---

## Project Structure

```
selph/
├── src/
│   ├── backend/app/
│   │   ├── routers/       auth, twin, drafts, messages, channels, identity, referrals
│   │   ├── services/      twin_engine, draft, identity, auth, moderation, twin_learning
│   │   ├── models/        user, twin, message, draft, identity_profile, briefing, sender_tier,
│   │   │                  message_cluster, batch_send, audit_log, consent, channel_credential
│   │   ├── channels/      gmail, instagram (OAuth + webhook adapters)
│   │   ├── voice/         chatterbox, elevenlabs providers (registry pattern)
│   │   ├── avatar/        linly-talker, heygen providers (registry pattern)
│   │   └── tasks/         draft_generation, voice_synthesis, avatar_generation, push_notifications
│   ├── web/               Next.js dashboard (Vercel)
│   └── mobile/            React Native app (iOS + Android)
├── docs/
│   ├── 01-product/        PRD, product vision
│   ├── 02-market/         validation, feature expansion
│   ├── 03-specs/          twin engine spec, identity model spec, feature expansion spec
│   ├── 04-safety/         risk mitigation, privacy, canonical policy matrix
│   ├── 05-technical/      system architecture, database schema, API design
│   └── 06-implementation/ MVP build plan, sprint plan, readiness scorecard, investor one-pager
├── docker-compose.yml     One command to run everything locally
└── DEMO.md                Step-by-step demo with live API calls
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

## Deployment

```bash
# Backend → Railway
railway up

# Web + Landing → Vercel (auto-deploys on push to main via GitHub Actions)
git push origin main
```

---

## Business Model

| Tier | Price | Who | What |
|---|---|---|---|
| **Free** | $0/mo | Everyone | 50 interactions/month, text twin |
| **Creator** | $39/mo | Influencers | Voice + avatar, 500 interactions, social channels |
| **Pro** | $99/mo | Consultants, Devs | Unlimited, all channels, private mode |
| **Executive** | $299/mo | Leaders | Priority, advanced analytics, enterprise security |
| **Enterprise** | Custom | Companies | Per-seat, SSO, compliance, SLA |

**North Star Metric:** Twin Approval Rate — % of drafts approved without edits.
Higher rate = twin sounds more like you = better product = stronger moat.

---

## Go-To-Market

```
Month 1–2   Private beta — 50 selected content creators
            Measure approval rate. Gather testimonials.

Month 3     Open waitlist. Creator referral program.
            PR: "The first AI that IS you, not just helps you."

Month 4–6   Pro tier — consultants, developers
            GitHub, Slack, Discord integrations live.

Month 7–12  Enterprise tier. SOC 2 certified.
            Team twins. Developer API.
```

Target: **1,000 active twins by Month 5** · **10,000 by Month 9** · **$50K MRR by Month 9**

---

## Why SELPH Wins

| Generic AI Agent | SELPH |
|---|---|
| Completes tasks | Completes tasks **as you** |
| Speaks as "AI" | Speaks in **your voice** |
| No personality | **Your personality** |
| Same output for everyone | **Unique to every user** |
| No trust model | **Graduated trust — earned over time** |
| Fragmented (chat / voice / avatar separately) | **Unified identity twin** |
| Reactive only | **Proactive — surfaces what you'd miss** |
| No creator scale | **Batch Pattern Approval — 50 replies in one tap** |

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

The canonical policy source of truth: [SELPH_Canonical-Policy-Matrix.md](docs/04-safety/SELPH_Canonical-Policy-Matrix.md)

---

## For Investors

SELPH is building the **identity layer for AI-native communication**.

- **82/100 build readiness** — not a deck, not a Figma mockup, a working system
- **9 phases shipped** — twin engine, voice clone, avatar clone, VIP tiers, batch approval, analytics
- **Strong moat** — identity models are personal, sticky, and continuously self-improving
- **Regulatory tailwind** — transparent AI interaction is what regulators want to see
- **Viral by design** — "I have a digital twin" is a 2026 status signal

[Read the full investor one-pager →](docs/06-implementation/INVESTOR_ONE_PAGER.md)

---

## For Developers

- **140+ LLM providers** via LiteLLM — BYOK or use defaults
- **OpenAPI docs** at `/docs` — fully typed, versioned endpoints
- **Webhook-ready** — Instagram and Gmail adapters included and tested
- **Registry pattern** — add new voice/avatar/channel providers without touching core logic
- **LangGraph StateGraph** — fully inspectable, interruptible, resumable twin pipeline

[Full API design →](docs/05-technical/SELPH_API-Design.md)

---

## Key Documents

| Document | What It Contains |
|---|---|
| [Product Vision](docs/01-product/PRODUCT_IDEA.md) | The idea, identity layers, operating modes, GTM waves |
| [PRD](docs/01-product/PRD.md) | Goals, user stories, features, business model |
| [System Architecture](docs/05-technical/SELPH_System-Architecture.md) | Full stack design, data flows, deployment |
| [Database Schema](docs/05-technical/SELPH_Database-Schema.md) | All tables, relationships, pgvector design |
| [API Design](docs/05-technical/SELPH_API-Design.md) | Every endpoint, request/response shapes |
| [Twin Engine Spec](docs/03-specs/SELPH_Twin-Engine-Spec.md) | LangGraph pipeline, confidence scoring, moderation |
| [Feature Expansion Spec](docs/03-specs/SELPH_Feature-Expansion-Spec.md) | Briefing, VIP tiers, batch approval, proactive twin |
| [Safety Policy Matrix](docs/04-safety/SELPH_Canonical-Policy-Matrix.md) | Canonical policy decisions, enforcement rules |
| [Build Readiness Scorecard](docs/06-implementation/BUILD_READINESS_SCORECARD.md) | 82/100 score, blockers, go/no-go decisions |
| [Investor One-Pager](docs/06-implementation/INVESTOR_ONE_PAGER.md) | Why now, competitive advantage, ask |

---

## Environment Variables

```bash
# Backend — .env (see .env.example for all options)
ANTHROPIC_API_KEY=sk-ant-...       # or any LiteLLM-supported key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET_KEY=...                  # 32+ chars in production
FIREBASE_PROJECT_ID=selph

# Web / Mobile
NEXT_PUBLIC_API_URL=http://localhost:8000
```

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

*Built April 2026 · All 9 phases complete · Ready for controlled creator pilot*

*SELPH — **S**elf · **E**cho · **L**ive · **P**roxy · **H**uman*

</div>
