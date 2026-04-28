# SELPH — Project Memory

> Quick-reference for AI assistants. Load CONTEXT.md for full detail.
> Last updated: 2026-04-27

---

## Project State

| Item | Value |
|---|---|
| **Status** | Implementation Plan complete — ready for Phase 0 code |
| **Docs** | 21 docs, all validated, stale-reference-free |
| **Repo** | Not created yet — `selph-ai` (GitHub, private) |
| **Next action** | Write Phase 0 backend code (`src/backend/`) |

---

## Stack (Non-negotiable)

```
Backend:   Python 3.11 + FastAPI + Celery + Redis
Database:  PostgreSQL 16 + pgvector  ← Railway managed, NO Pinecone
LLM:       LiteLLM → claude-sonnet-4-6 (default)
Voice:     Chatterbox (MIT, default) — ElevenLabs = paid optional only
Avatar:    Linly-Talker (MIT, default) — HeyGen = paid optional only
Hosting:   Railway (backend) + Vercel (web + landing) + Cloudflare (R2 + DNS)
Auth:      JWT RS256
Mobile:    React Native (Expo)
Web:       Next.js 15 — app.selph.ai (dashboard)
Landing:   Next.js 15 static — selph.ai (marketing)
Shared:    @selph/shared (npm workspace — API client, types, constants)
```

---

## Decisions That Must Not Be Revisited

| Decision | Reason |
|---|---|
| No AWS | Replaced with Railway + Cloudflare + Vercel |
| No Pinecone | pgvector on Railway PostgreSQL |
| No Kafka | Celery + Redis for MVP |
| No ClickHouse | audit_logs table in PostgreSQL |
| Chatterbox = default voice | Free, MIT, open-source |
| Linly-Talker = default avatar | Free, MIT, open-source |
| Light UI (not dark) | User rejected dark cinematic — v3.0 is light + colorful |
| Single architecture doc | SELPH_Modern-Architecture.md was deleted |
| /v1/ prefix on all API routes | Mobile App Store — can't break URLs |
| src/ at repo root | docs/ and src/ are siblings |
| landing/ separate from web/ | Two domains, two Vercel deployments |

---

## Repo Layout (One-liner)

```
selph-ai/docs/  src/backend/  src/web/  src/landing/  src/mobile/  src/shared/  src/services/
```

---

## UI Design — v3.0 Light & Colorful

```
Canvas:   white #FFFFFF / warm-white #FAFAF9
Primary:  violet #7C3AED  →  sky #0EA5E9  (gradient)
Energy:   coral #F43F5E  →  orange #F97316
Success:  emerald #10B981
Text:     #0F172A (title) / #334155 (body) / #64748B (muted)
Semantic: #10B981 approve / #F59E0B edit / #EF4444 reject
Fonts:    Plus Jakarta Sans + Inter + JetBrains Mono
Motion:   spring physics, conic spinning identity ring, swipe-to-approve mobile
```

---

## Key Patterns (Copy-paste Ready)

```python
# Channel adapter — never hardcode channel name
from app.channels.registry import get_adapter
adapter = get_adapter("instagram_dm")

# Service calls — always through registry
from app.services.registry import services
profile = services.identity.get_profile(user_id)
draft   = services.twin_engine.run_pipeline(message, profile)

# Feature flag check
from app.config import settings
if settings.FEATURE_INSTAGRAM_DM:
    ...

# Confidence labels
HIGH   = 0.85+   # "Ready to send"
MEDIUM = 0.65+   # "Review suggested"
LOW    = <0.65   # "Needs your input"
```

```typescript
// Shared API client — web + mobile both use this
import { api } from '@selph/shared/api'
const drafts = await api.drafts.getPending()
await api.drafts.action(id, 'approve')
```

---

## Phase 0 Checklist (Start Here)

```
[ ] GitHub repo created: selph-ai (private)
[ ] src/backend/ — docker-compose up (postgres + redis + api + worker)
[ ] GET /health → 200
[ ] POST /v1/auth/signup → creates user + twin
[ ] POST /v1/auth/login → JWT token
[ ] Alembic migrations run, pgvector enabled
[ ] src/shared/ — @selph/shared package scaffolded
[ ] src/web/ — Next.js dashboard loads, Tailwind tokens applied
[ ] src/landing/ — Next.js static site loads
[ ] src/mobile/ — Expo app loads on simulator
[ ] Railway backend deployed → /health returns 200
[ ] Vercel web deployed → dashboard loads
```

---

## Files to Read for Full Context

| Need | Read |
|---|---|
| Everything | `SELPH/CONTEXT.md` |
| Repo structure + code | `docs/06-implementation/IMPLEMENTATION_PLAN.md` |
| Build phases | `docs/06-implementation/MVP_BUILD_PLAN.md` |
| Architecture | `docs/05-technical/SELPH_System-Architecture.md` |
| Database schema | `docs/05-technical/SELPH_Database-Schema.md` |
| Twin engine design | `docs/03-specs/SELPH_Twin-Engine-Spec.md` |
| UI/UX design | `docs/07-design/SELPH_UI-UX-Design.md` |
| Safety rules | `docs/04-safety/SELPH_Canonical-Policy-Matrix.md` |
