<div align="center">
<br/>

![SELPH](assets/hero.svg)

<br/>

[![CI](https://github.com/VenkataAnilKumar/SELPH/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/VenkataAnilKumar/SELPH/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/release-v1.0.0--rc-blue?style=flat-square)](https://github.com/VenkataAnilKumar/SELPH/releases/tag/v1.0.0-rc)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%C2%B7%20PostgreSQL%20%C2%B7%20pgvector-009688?style=flat-square)](#architecture)
[![Apps](https://img.shields.io/badge/apps-Next.js%20%C2%B7%20Expo-black?style=flat-square)](#architecture)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey?style=flat-square)](LICENSE)

**An AI digital twin that drafts your replies in your voice, and sends nothing until you approve it.**

[Try it in 5 minutes](#try-it-in-5-minutes) · [How it works](#how-it-works) · [Safety](#safety-and-privacy) · [Architecture](#architecture) · [Docs](#documentation)

<br/>
</div>

---

## Why SELPH

Creators can't answer thousands of DMs. Consultants repeat the same answers every day. Executives drown in email. Generic AI helps with tasks, but it doesn't sound like you, and you can't trust it to speak for you.

SELPH learns how you write, drafts a reply to each incoming message, and puts you in control: **approve, edit, reject or skip, every time.** Every decision teaches your twin. VIPs never touch it. Sensitive messages are handed back to you instead of answered with a template.

<div align="center">

![SELPH landing page](demo/landing.png)

</div>

## See it

<table>
<tr>
<td width="55%" valign="top">

**Review every draft.** Each reply shows its confidence and where it came from. Risky messages are flagged with the reason, and flagged drafts are never sent automatically.

![Pending drafts with a flagged message](demo/dashboard-drafts.png)

</td>
<td width="45%" valign="top">

**Steer your twin.** Tell it something once with a *briefing* ("at a conference, keep it short"). Mark people as *VIP* so their messages skip the twin entirely.

![Briefings and VIP senders](demo/dashboard-controls.png)

</td>
</tr>
</table>

<details>
<summary><b>Phone layout</b> and the <b>trust section</b> of the landing page</summary>
<br/>

<table>
<tr>
<td width="25%" valign="top"><img src="demo/dashboard-phone.png" alt="Dashboard on a phone"/></td>
<td valign="top"><img src="demo/landing-trust.png" alt="Safety principles on the landing page"/></td>
</tr>
</table>

</details>

## What you get

| | |
|---|---|
| **Drafts in your voice** | Six onboarding questions seed your tone, length and boundaries. A built-in drafter works with **no API key**. Add a model of your choice (via LiteLLM, including local models) for richer drafts. |
| **You approve everything** | Approve, edit, reject or skip. Approved drafts on connected channels are delivered once and retried on transient failures. Simulated messages never leave the system. |
| **Twin Briefing** | Time-boxed context injected into every draft: availability, instructions, facts, opinions, boundaries. |
| **VIP tiers** | Tier 0 bypasses the twin and notifies you directly. Tier 1 always forces review. |
| **Batch approval** | Fifty people ask the same thing? Approve one template, and each recipient gets a personalized copy. |
| **Learns from you** | Approvals and edits feed a confidence score that reflects what you actually accept, not just profile completeness. |
| **Verifiable replies** | Approved replies are signed so a recipient can check they came from your twin. |
| **Voice and avatar (optional)** | Consent-gated. A mock provider is the default; ElevenLabs and HeyGen are supported when you add keys. |
| **Crisis and proactive tools** | Crisis mode, surge detection, proactive suggestions, style-evolution checkpoints, and twin-to-twin sessions. |

**Two modes.** *Transparent* labels replies as coming from your digital twin (good for creators). *Private* sends them as you, because you approved every one (good for consultants and executives).

## How it works

```mermaid
flowchart TB
    A["Instagram DM or Gmail"] -->|"webhook, signature verified"| B["Ingest message"]
    B --> C{"Who is it from?"}
    C -->|"VIP (tier 0)"| V["Notify you directly<br/>no draft"]
    C -->|"twin paused"| P["No draft"]
    C -->|"anyone else"| D["Twin engine<br/>profile + briefings + history"]
    D --> M["Safety checks<br/>harmful, injection, sensitive"]
    M --> Q["Pending drafts"]
    Q -->|"approve or edit"| S["Deliver through the channel"]
    Q -->|"reject or skip"| X["Nothing is sent<br/>twin learns"]
    S --> L[("Audit log and<br/>signed reply")]
```

Without a connected account (for example when you try the app locally), the **Simulate Incoming Message** panel lets you run the whole loop with nothing leaving your machine.

## Try it in 5 minutes

You need **no AI key and no Instagram or Gmail account**. Prerequisites: Docker, and Node 20+.

```bash
git clone https://github.com/VenkataAnilKumar/SELPH.git
cd SELPH

# 1. Backend: PostgreSQL + pgvector, Redis, API (runs migrations), worker
docker compose up --build

# 2. Web app, in another terminal
npm ci
cd src/web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

| | |
|---|---|
| Web app | <http://localhost:3000> |
| API docs | <http://localhost:8000/docs> |
| Health / readiness | <http://localhost:8000/health> · <http://localhost:8000/ready> |

Sign up, open the dashboard, and use **Simulate Incoming Message**: watch your twin draft a reply, then approve, edit or reject it.

<details>
<summary><b>No Docker?</b> Run the backend directly</summary>

```bash
cd src/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql://selph:selph_dev_password@127.0.0.1:5432/selph   # Postgres 16 with pgvector
export REDIS_URL=redis://127.0.0.1:6379/0
alembic upgrade head
uvicorn app.main:app --port 8000
```

Load realistic demo data (an onboarded twin, briefings, VIP tiers, pending and decided drafts):

```bash
python scripts/seed_dev.py        # demo@example.com / DemoPass!234
```

Smoke-test the whole API against the running server:

```bash
python scripts/local_e2e.py
```

</details>

A guided walkthrough with every request is in **[DEMO.md](DEMO.md)**.

### Add a real model (optional)

```bash
FEATURE_TWIN_LLM_DRAFTS=true
DEFAULT_LLM_MODEL=claude-sonnet-4-6      # any LiteLLM model, e.g. ollama/llama3.1 for fully local
ANTHROPIC_API_KEY=...                    # or OPENAI_API_KEY / GOOGLE_API_KEY
```

If the model fails or returns something unusable, SELPH falls back to the built-in drafter automatically.

## Safety and privacy

Trust is the product, so these are enforced in code and covered by tests (see **[Security acceptance criteria](docs/04-safety/SECURITY_ACCEPTANCE_CRITERIA.md)**).

- **Nothing sends without your decision.** Approving is the only path to delivery. A draft can't be decided twice, so a reply is never delivered twice.
- **Flagged drafts need you.** Drafts that touch financial, legal or medical direction, and messages about self-harm or asking for such advice, are flagged with the reason and never auto-delivered.
- **Hostile text isn't obeyed.** "Ignore your instructions"-style messages are flagged, and untrusted inbound text never steers the twin.
- **No invented facts.** The built-in drafter never makes up prices, dates, links or promises. Questions get an honest "let me get back to you". A 50-case golden-prompt suite (≥95% required in CI) guards this.
- **One-tap pause** stops all drafting immediately.
- **Webhooks fail closed.** Instagram and Gmail webhooks are rejected unless their signing secret is configured.
- **Credentials encrypted at rest.** Channel tokens and twin signing keys use Fernet encryption with key rotation. Logout revokes tokens server-side, and refresh tokens are single-use.
- **You own your data.** Export everything as JSON, or delete your account and receive a signed, publicly verifiable deletion certificate. Audit logs are kept anonymized.

## Architecture

```mermaid
flowchart TB
    subgraph Clients
        W["Web<br/>Next.js"]
        M["Mobile<br/>Expo / React Native"]
        L["Landing<br/>static site"]
    end

    subgraph Backend["FastAPI backend"]
        API["REST API /v1"]
        E["Twin engine<br/>LangGraph"]
        S["Safety checks"]
    end

    W --> API
    M --> API
    L -. "sign-up link" .-> W
    API --> E --> S
    API --> PG[("PostgreSQL<br/>+ pgvector")]
    API --> R[("Redis")]
    R --> K["Celery workers"]
    K --> CH["Instagram / Gmail"]
    K --> PN["Push notifications"]
    E -. "optional" .-> LLM["LLM via LiteLLM"]
```

| Layer | Technology |
|---|---|
| API | FastAPI, SQLAlchemy 2, Alembic (11 migrations), Pydantic |
| Data | PostgreSQL 16 with pgvector, Redis |
| Jobs | Celery workers (delivery, push, voice, avatar) |
| AI | Built-in drafter by default; LiteLLM for 100+ models (BYOK or local); optional ElevenLabs / HeyGen |
| Web | Next.js 15, React 18, Tailwind |
| Mobile | Expo, React Native |
| Observability | Prometheus `/metrics`, structured audit log ([details](docs/06-implementation/OBSERVABILITY.md)) |

<details>
<summary><b>Repository layout</b></summary>

```
src/
├── backend/          FastAPI service
│   ├── app/          routers, services, models, channels, tasks, voice, avatar
│   ├── migrations/   Alembic revisions
│   ├── evals/        golden-prompt quality gate
│   ├── scripts/      seed, e2e, migration round-trip, credential encryption
│   └── tests/
├── web/              Next.js dashboard
├── mobile/           Expo app
├── landing/          static marketing site
└── shared/           typed API client used by web and mobile
demo/                 screenshots of the product, plus the script that retakes them
docs/                 product, specs, safety, technical, implementation
scripts/              browser end-to-end test
```

</details>

## Configuration

Everything is environment-driven. Copy `src/backend/.env.example` for the full, commented list. The ones that matter most:

| Variable | Purpose |
|---|---|
| `DATABASE_URL`, `REDIS_URL` | Postgres and Redis |
| `JWT_SECRET_KEY` | Signs sessions. Use 32+ random characters in production |
| `CREDENTIAL_ENCRYPTION_KEY` | Encrypts channel tokens. **Required in production** |
| `META_APP_SECRET`, `GOOGLE_WEBHOOK_SECRET` | Webhook signing secrets. Webhooks are rejected without them |
| `FEATURE_TWIN_LLM_DRAFTS`, `DEFAULT_LLM_MODEL` | Turn on model-written drafts |
| `AUTO_SEND_ON_APPROVE` | Deliver approved drafts automatically (default on) |
| `METRICS_TOKEN` | Protects `/metrics` (hidden in production without it) |

`GET /ready` reports exactly which of these are missing.

## Quality

```bash
npm test                                   # web, mobile and landing suites
cd src/backend && pytest tests/            # 430+ backend tests
cd src/backend && python -m evals.run_evals   # golden prompts (>= 95% required)
node scripts/browser_e2e.js ./screenshots  # real-browser end-to-end run (needs Playwright + the stack)
```

CI runs all of this, plus type-checking for web, landing and mobile, production builds, a migration round-trip (up, down one revision at a time, up), and an erasure test against real Postgres with enforced foreign keys.

## Status

**Works today** (verified end to end locally, without an LLM key): the full draft, approve, edit, reject loop; briefings; VIP bypass; batch approval; pause; safety flagging; export and erasure; metrics; web dashboard; landing site.

**Needs your setup before real use:**

- **Instagram and Gmail** require your own Meta and Google developer apps (Instagram needs a Business account and app review). The integrations are built but haven't been exercised against live accounts.
- **Draft quality with a real model** hasn't been measured yet. The built-in drafter produces safe scaffolds you edit, not finished prose.
- **Deployment**: `docker compose up --build` builds and starts the whole backend (Postgres + pgvector, Redis, API with migrations, worker, Flower), and CI builds and exercises that stack on every change. It is a development stack: production hosting, TLS and secrets are yours to provision. Follow the production checklist in the [security criteria](docs/04-safety/SECURITY_ACCEPTANCE_CRITERIA.md#production-checklist).

**Honest notes:**

- The twin engine is a LangGraph pipeline (context, draft with one retry, safety checks, routing, audit). It runs straight through: the saved pending draft is the human checkpoint, and approving is the resume. Every draft writes a structured audit event with risk, priority and latency.
- Voice and avatar models held by third-party providers aren't deleted by account erasure, because the provider integrations have no delete call. The deletion certificate says so.

**Planned:** open-source voice and avatar providers, more channels, and content provenance (C2PA).

## Documentation

| | |
|---|---|
| [DEMO.md](DEMO.md) | Hands-on walkthrough with every API call |
| [demo/](demo/README.md) | Screenshots of the product, with captions and how to link them |
| [Product vision](docs/01-product/PRODUCT_IDEA.md) · [PRD](docs/01-product/PRD.md) | What and why |
| [System architecture](docs/05-technical/SELPH_System-Architecture.md) · [API design](docs/05-technical/SELPH_API-Design.md) · [Database schema](docs/05-technical/SELPH_Database-Schema.md) | How it's built |
| [Safety policy](docs/04-safety/SELPH_Canonical-Policy-Matrix.md) · [Privacy and consent](docs/04-safety/SELPH_Privacy-Consent.md) · [Security criteria](docs/04-safety/SECURITY_ACCEPTANCE_CRITERIA.md) | Trust |
| [Observability](docs/06-implementation/OBSERVABILITY.md) | Metrics, SLO queries, alerts |
| [CHANGELOG](CHANGELOG.md) | What changed |

## Contributing

Contributions are by invitation only. If you're on the core team, read **[CONTRIBUTING.md](CONTRIBUTING.md)** for branch naming, commit style, PR process and code standards.

Found a bug? Open a GitHub issue. Security vulnerability? Email **vanilkumarch@gmail.com** directly. Please don't open a public issue.

## License

Copyright © 2026 Venkata Anil Kumar. All rights reserved. Proprietary software: no part may be used, copied, modified or distributed without express written permission. See **[LICENSE](LICENSE)**.

<br/>

<div align="center">

*Be everywhere. Be SELPH.*

*Interested in a pilot, or have questions? [vanilkumarch@gmail.com](mailto:vanilkumarch@gmail.com)*

<br/>
</div>
