# SELPH — Deployment & Pilot Plan

> Version: 1.0
> Created: 2026-04-30
> Status: Active — Phases 11–16, post v1.0.0-rc
> Prerequisite: [BUILD_READINESS_SCORECARD.md](./BUILD_READINESS_SCORECARD.md) — current score 88/100, CI green
> Related: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — code-level build guide (Phases 0–10, complete)

---

## Context

Phases 0–10 are built, tested, and CI-validated (`v1.0.0-rc`, commit `2da484c`).
287 backend tests, 23 web tests, 32 mobile tests, and 7 migration smoke tests are all passing.

This document covers the remaining path from green CI to live pilot:

| Phase | Focus | Target Window |
|---|---|---|
| 11 | Railway production infra provisioning | Week 1–2 |
| 12 | LiteLLM + real draft generation | Week 2–3 |
| 13 | Channel integration (Instagram → Gmail) | Week 3–5 |
| 14 | Observability and SLO instrumentation | Week 4–5 |
| 15 | Security hardening | Week 4–5 |
| 16 | Pilot launch — first 5 creators | Week 6 |

---

## Phase 11 — Railway Production Infrastructure

**Goal:** Backend reachable at `https://api.selph.ai` with database, queue, and workers running.

### Services to Provision

| Service | Railway setup | Notes |
|---|---|---|
| FastAPI API | New service from GitHub repo; root `/src/backend`; `Dockerfile` | Set `PORT` env var |
| PostgreSQL | Railway managed Postgres add-on | Must enable pgvector plugin after provision |
| Redis | Railway managed Redis add-on | Used by Celery broker + result backend |
| Celery Worker | Second service, same image; override `CMD` | `celery -A app.celery_app worker --loglevel=info` |
| Celery Beat | Third service or Railway Cron job | `celery -A app.celery_app beat --loglevel=info` |

### pgvector on Railway PostgreSQL

After provisioning the managed Postgres, connect via psql and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then run migrations:

```bash
railway run --service selph-api -- python -m alembic -c alembic.ini upgrade head
```

### Environment Variables (set in Railway dashboard)

```
DATABASE_URL          postgresql://<user>:<pass>@<host>:<port>/railway
REDIS_URL             redis://default:<pass>@<host>:<port>
SECRET_KEY            <64-char random string — never reuse dev key>
ENVIRONMENT           production
LLM_API_KEY           <set in Phase 12>
LITELLM_MODEL         claude-sonnet-4-6
INSTAGRAM_APP_SECRET  <set in Phase 13>
INSTAGRAM_VERIFY_TOKEN <set in Phase 13>
GMAIL_CLIENT_ID       <set in Phase 13>
GMAIL_CLIENT_SECRET   <set in Phase 13>
FIREBASE_CREDENTIALS  <base64-encoded service account JSON>
```

### DNS and TLS

1. Add custom domain `api.selph.ai` in Railway service settings.
2. In Cloudflare DNS: add CNAME `api` → Railway-provided domain; proxy enabled.
3. TLS terminates at Cloudflare (full strict mode).
4. Add Cloudflare WAF rule: block requests with no `User-Agent` header to `/v1/*`.

### Cloudflare R2 Storage

```bash
# Create bucket for voice and avatar assets
wrangler r2 bucket create selph-assets

# Set CORS policy for mobile app origin
# Set in R2 bucket settings: allowed origins = https://app.selph.ai
```

Set env vars on Railway:
```
R2_ACCOUNT_ID     <Cloudflare account ID>
R2_ACCESS_KEY_ID  <R2 API token key ID>
R2_SECRET_KEY     <R2 API token secret>
R2_BUCKET         selph-assets
```

### Done When

- [ ] `GET https://api.selph.ai/health` returns `{"status": "ok"}`
- [ ] `GET https://api.selph.ai/ready` returns all checks green
- [ ] Migrations applied: `alembic current` shows `008_phase10_end_to_end_foundation (head)`
- [ ] Celery worker is running and consuming from queue (check Railway logs)
- [ ] R2 bucket reachable from backend (upload + download test file)

---

## Phase 12 — LiteLLM and Real Draft Generation

**Goal:** Send a message to the API and receive a real AI-generated draft in the user's voice.

### Steps

1. Set `LLM_API_KEY` (Anthropic Claude or OpenAI) in Railway environment.
2. Set `LITELLM_MODEL=claude-sonnet-4-6` (or `gpt-4o` if using OpenAI).
3. Run end-to-end smoke test manually:
   ```bash
   # 1. Register a test user
   curl -X POST https://api.selph.ai/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@selph.ai","password":"Test1234!","full_name":"Test User"}'

   # 2. Trigger a draft
   curl -X POST https://api.selph.ai/v1/twin/draft \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"channel":"instagram","message":"Hey love your content!"}'

   # 3. Verify draft returned with content
   ```
4. Validate cost tracking: check `twin_stats` row for `model_breakdown` field populated.
5. Test BYOK path: set user-level `llm_api_key` override and confirm it routes correctly.

### Latency Target

- p95 draft generation < 3 seconds (track from message ingest to draft available).

### Done When

- [ ] End-to-end manual smoke: message in → draft back in < 3 s.
- [ ] Cost tracking row written per draft.
- [ ] BYOK path routes to user-supplied key.

---

## Phase 13 — Channel Integration

### 13A — Instagram DMs

**Goal:** Real Instagram DMs flow into SELPH and trigger draft generation.

#### Setup Steps

1. Create a Meta Developer App at `developers.facebook.com`.
2. Add Instagram product; set webhook URL: `https://api.selph.ai/webhooks/instagram`.
3. Set `INSTAGRAM_VERIFY_TOKEN` in Railway (any random string; must match Meta app config).
4. Set `INSTAGRAM_APP_SECRET` in Railway (used for HMAC webhook signature verification).
5. Request permissions: `instagram_manage_messages`, `pages_messaging`.
6. Submit for App Review (required for production; sandbox works without review for test accounts).

#### Onboarding UI

Build a guided connect flow in the web/mobile app:

```
Step 1: "Switch to a Professional Account on Instagram"
        [Open Instagram Settings →]

Step 2: "Connect your Facebook Page"
        [Connect Page →] → OAuth flow → store page token

Step 3: "Test it — send yourself a DM"
        [Send test DM →] → verify webhook fires → draft appears
```

#### Webhook Verification

The backend already has the `/webhooks/instagram` endpoint. Verify HMAC signature check is active:

```python
# src/backend/app/routers/channels.py
# Confirm: X-Hub-Signature-256 header validated before processing payload
```

#### Done When

- [ ] Webhook `GET` verification handshake passes (Meta sends challenge, backend echoes it).
- [ ] Test DM from sandbox account triggers draft creation in database.
- [ ] HMAC signature check blocks unsigned requests.
- [ ] Guided onboarding flow navigable end-to-end in mobile app.

---

### 13B — Gmail

**Goal:** Incoming Gmail messages flow into SELPH and trigger draft generation.

#### Setup Steps

1. Create a Google Cloud project; enable Gmail API and Cloud Pub/Sub API.
2. Create a Pub/Sub topic: `selph-gmail-notifications`.
3. Create a push subscription pointing to `https://api.selph.ai/webhooks/gmail`.
4. Grant Gmail service account `roles/pubsub.publisher` on the topic.
5. Set env vars in Railway:
   ```
   GMAIL_CLIENT_ID       <OAuth 2.0 client ID>
   GMAIL_CLIENT_SECRET   <OAuth 2.0 client secret>
   GMAIL_PUBSUB_TOPIC    projects/<project>/topics/selph-gmail-notifications
   ```
6. Implement `gmail.users.watch()` call on user OAuth token to start push notifications.
7. Implement Celery beat task to renew `watch()` every 6 days (watch expires at 7 days).

#### Onboarding UI

```
Step 1: "Connect your Gmail"
        [Sign in with Google →] → OAuth consent → store refresh token

Step 2: "Choose which emails your twin monitors"
        ○ All inbox  ○ Labeled only: [___________]

Step 3: "Send yourself a test email"
        [Send test →] → verify push notification fires → draft appears
```

#### Done When

- [ ] OAuth flow completes; refresh token stored (encrypted at rest).
- [ ] `watch()` subscription active; Pub/Sub push fires on new email.
- [ ] Test email triggers draft creation.
- [ ] Beat task renews `watch()` before 7-day expiry.

---

## Phase 14 — Observability

**Goal:** Know when something is wrong before users do.

### SLOs to Instrument

| SLO | Target | Alert threshold |
|---|---|---|
| p95 draft latency | < 3 s | > 5 s for 5 min |
| p99 draft latency | < 8 s | > 12 s for 5 min |
| API error rate | < 1% | > 2% for 5 min |
| Celery queue lag | < 10 s | > 30 s for 5 min |
| Moderation false-positive rate | < 5% | > 10% over 1 h |
| Approval funnel: approve rate | > 60% | < 40% over 1 h (twin quality signal) |

### Implementation

1. Add `prometheus-fastapi-instrumentator` to `requirements.txt`.
2. Mount metrics endpoint in `main.py`:
   ```python
   from prometheus_fastapi_instrumentator import Instrumentator
   Instrumentator().instrument(app).expose(app, endpoint="/metrics")
   ```
3. Add custom Celery task duration histogram via `prometheus_client`.
4. Use Railway built-in metrics for CPU/memory/disk baseline.
5. For dashboards: Grafana Cloud free tier (10k metrics, 14-day retention).
6. Configure alerts: email + Slack webhook on SLO breach.

### Done When

- [ ] `GET https://api.selph.ai/metrics` returns Prometheus text format.
- [ ] p95 latency and error rate visible in Grafana dashboard.
- [ ] At least one alert fires correctly in test.

---

## Phase 15 — Security Hardening

**Goal:** Pass internal security review before any external user touches the system.

### Checklist

#### Token Encryption at Rest
- [ ] OAuth access/refresh tokens stored with Fernet symmetric encryption (key from env var `TOKEN_ENCRYPTION_KEY`).
- [ ] Existing `oauth_tokens` rows migrated (one-time script).

#### Webhook Signature Verification
- [ ] Instagram: `X-Hub-Signature-256` HMAC-SHA256 verified on every inbound webhook — confirm this is not skippable.
- [ ] Gmail: Pub/Sub push message JWT verified using Google's public JWKS endpoint.

#### Deletion Certificate Workflow
- [ ] `DELETE /v1/privacy/delete-account` endpoint triggers: soft-delete user record, queue hard-delete job for 30 days, issue signed deletion certificate (stored in R2), notify user by email.
- [ ] Celery task executes hard delete after retention window.

#### Auth Rate Limiting
- [ ] `POST /auth/register` and `POST /auth/login` limited to 10 req/min per IP in production.
- [ ] `POST /auth/refresh` limited to 30 req/min per user.

#### OWASP Scan
- [ ] Run OWASP ZAP baseline scan against staging Railway deployment.
- [ ] Fix all High and Medium findings before pilot.

### Done When

- [ ] OAuth tokens encrypted; decryption tested.
- [ ] Both webhook signature checks enforced and tested with invalid signatures.
- [ ] Deletion certificate issued and retrievable.
- [ ] Rate limiting active; returns `429` on breach.
- [ ] ZAP scan shows no High findings.

---

## Phase 16 — Pilot Launch

**Goal:** 5 real creators using SELPH for Instagram DMs, generating and approving drafts.

### Pre-Launch Checklist

- [ ] Phase 11: all infra green, `/ready` all-pass.
- [ ] Phase 12: real drafts generating in < 3 s p95.
- [ ] Phase 13: Instagram DM flow tested with real Business Account.
- [ ] Phase 14: SLO dashboard live, alerts configured.
- [ ] Phase 15: security review passed.
- [ ] Web app deployed to Vercel (`app.selph.ai`).
- [ ] React Native app on TestFlight (iOS) and internal Android track.
- [ ] Support contact set up (`support@selph.ai`).

### Pilot KPIs (track from Day 1)

| Metric | Target | Meaning |
|---|---|---|
| Draft approval rate | > 60% | Twin sounds like the user |
| Draft edit rate | < 30% | Twin is close but needs polish |
| Draft reject rate | < 10% | Twin is missing something |
| Time-to-approve | < 5 s median | Approval UX is frictionless |
| p95 draft latency | < 3 s | System is fast enough |
| Messages processed per user per day | > 10 | Real usage, not just setup |

### Pilot Cohort

- 5 creators, Instagram-first
- Mix of follower counts: 2 micro (10k–100k), 2 mid (100k–500k), 1 large (500k+)
- Direct recruitment via `vanilkumarch@gmail.com`
- Weekly 30-minute check-in call during pilot period

### Done When

- [ ] 5 creators onboarded and connected.
- [ ] 100 drafts generated across cohort.
- [ ] Approval rate > 60% sustained for 3 days.
- [ ] No P0/P1 incidents in first week.

---

## Execution Timeline

```
Apr 30 – May 7  (Week 1)   Phase 11A: Railway services provisioned, migrations applied
May 7  – May 10 (Week 2)   Phase 11B: DNS, TLS, R2, /ready all-green
May 10 – May 14 (Week 2–3) Phase 12:  LiteLLM wired, real drafts working
May 14 – May 21 (Week 3–4) Phase 13A: Instagram integration live
May 21 – May 25 (Week 4)   Phase 13B: Gmail integration live
May 21 – May 28 (Week 4–5) Phase 14:  Observability instrumented
May 21 – May 28 (Week 4–5) Phase 15:  Security hardened (parallel with 14)
May 28 – Jun 4  (Week 6)   Phase 16:  Pilot launch — 5 creators onboarded
```

---

## Open Questions Before Execution

1. **Railway plan** — Starter plan ($5/month per service) or Team plan? Five services = ~$25/month minimum.
2. **LLM provider** — Anthropic Claude (default) or OpenAI? Affects `LLM_API_KEY` and cost model.
3. **Meta App Review** — Instagram requires app review for production. Submit immediately; review takes 5–10 days.
4. **Vercel / React Native deployment** — Are app store accounts (Apple Developer + Google Play) set up?
