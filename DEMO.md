# SELPH — Local Walkthrough

Run the whole product on your machine: **no LLM key, no Instagram/Gmail account, no cloud**.
Every command below was run against the real API.

Without an LLM, SELPH uses its built-in **fallback drafter**: it recognizes what a message is
(question, thanks, meeting request, business inquiry), matches your tone and reply length,
honors availability briefings, and never invents facts. Questions get a
"let me get back to you" scaffold that you edit before approving. Add an LLM later for richer drafts
(see [Optional: real LLM](#optional-real-llm)).

---

## 1. Start the stack

### Option A — Docker

```bash
docker compose up --build   # runs migrations automatically; optional LLM vars are passed from your shell
```

### Option B — No Docker (Postgres 16 + pgvector + Redis installed locally)

```bash
cd src/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://selph:selph_dev_password@127.0.0.1:5432/selph
export REDIS_URL=redis://127.0.0.1:6379/0
alembic upgrade head
uvicorn app.main:app --port 8000
```

API: <http://localhost:8000> · Interactive docs: <http://localhost:8000/docs>

> Celery and Redis are only needed for push notifications and voice/avatar jobs. Draft generation
> through `/v1/messages/ingest` runs inline, and a missing broker never blocks drafting.

### Start the web app

```bash
npm ci
cd src/web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open <http://localhost:3000>, sign up, and use **Simulate Incoming Message** on the dashboard.

### Or run the whole scripted check

```bash
cd src/backend && python scripts/local_e2e.py
```

It signs up a fresh user and exercises everything in this document, exiting non-zero on any failure.

---

## 2. The approval loop (API)

```bash
BASE=http://localhost:8000/v1
```

### Sign up

```bash
curl -s -X POST $BASE/auth/signup -H "Content-Type: application/json" \
  -d '{"email":"maya@example.com","password":"Str0ngPass!234","name":"Maya Chen"}'
```

Returns `{"user": {...}, "tokens": {"access_token": "...", "refresh_token": "..."}}`.
A twin is created for you automatically.

```bash
TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"maya@example.com","password":"Str0ngPass!234"}' | jq -r .tokens.access_token)
AUTH="Authorization: Bearer $TOKEN"
```

### Teach your twin who you are

```bash
curl -s -X POST $BASE/identity/onboard -H "$AUTH" -H "Content-Type: application/json" -d '{
  "role": "AI creator and educator",
  "communication_style": "friendly",
  "topics_avoided": ["politics", "religion"],
  "response_length": "short",
  "audience_tone": "warm and encouraging",
  "three_words": ["curious", "direct", "kind"]
}'
```

`communication_style`: `formal | casual | friendly | direct | humorous` ·
`response_length`: `short | medium | detailed`.

```bash
curl -s -X POST $BASE/identity/topics/known -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"topic": "agentic AI"}'
```

### Twin Briefing — tell it something once

```bash
curl -s -X POST $BASE/identity/briefings -H "$AUTH" -H "Content-Type: application/json" -d '{
  "briefing_type": "availability",
  "topic": "conference week",
  "content": "I am at a conference this week, so replies may be slower",
  "priority": 8
}'
```

`briefing_type`: `fact | opinion | instruction | availability | boundary`.
Availability briefings are added to drafts as a heads-up line.

### VIP tiers — some people never reach the twin

```bash
curl -s -X PUT $BASE/identity/sender-tiers -H "$AUTH" -H "Content-Type: application/json" -d '{
  "sender_id": "cofounder_1", "platform": "instagram_dm", "tier": 0, "tier_label": "Co-founder"
}'
```

Tier `0` bypasses the twin entirely, tier `1` always forces review. `platform` must match the channel
of the incoming message.

### Receive a message

```bash
curl -s -X POST $BASE/messages/ingest -H "$AUTH" -H "Content-Type: application/json" -d '{
  "channel": "instagram_dm",
  "sender_id": "fan_1",
  "sender_name": "Priya Rao",
  "content": "Loved your talk! How do you stay focused while building AI products?"
}'
```

```json
{
  "message_id": "…",
  "status": "draft_ready",
  "routing_action": "notify_user",
  "tier": 2,
  "draft_id": "…",
  "generation_source": "deterministic"
}
```

A VIP sender returns `"routing_action": "direct_notify"` with no `draft_id`.
A paused twin returns `"routing_action": "skipped_manual_pause"` with no `draft_id`.

### Review, then approve, edit, reject, or skip

```bash
curl -s $BASE/drafts/pending -H "$AUTH"
curl -s $BASE/drafts/DRAFT_ID -H "$AUTH"
```

All four decisions use the same endpoint:

```bash
# approve as-is
curl -s -X POST $BASE/drafts/DRAFT_ID/approve -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"action": "approve"}'

# edit, then approve (the twin learns from your edit)
curl -s -X POST $BASE/drafts/DRAFT_ID/approve -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"action": "edit", "edited_content": "Hey Priya! I keep a short list of 3 people I follow closely."}'

# reject / skip
curl -s -X POST $BASE/drafts/DRAFT_ID/approve -H "$AUTH" -H "Content-Type: application/json" -d '{"action": "reject"}'
curl -s -X POST $BASE/drafts/DRAFT_ID/approve -H "$AUTH" -H "Content-Type: application/json" -d '{"action": "skip"}'
```

Nothing is ever sent without one of these actions. Each approved or edited draft gets a signed
verification certificate (`GET /v1/twin/certificate`, `GET /verify/{twin_id}/{message_hash}`).

---

## 3. Creator scale: Batch Approval

When many people ask the same thing, cluster the pending drafts and approve one template:

```bash
curl -s -X POST $BASE/drafts/batches/cluster -H "$AUTH" -H "Content-Type: application/json" -d '{}'

curl -s -X POST $BASE/drafts/batches/CLUSTER_ID/approve -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"template_approved": "Hey {sender_name}! I mostly use Claude Code and LangGraph."}'

curl -s $BASE/drafts/batches/CLUSTER_ID/sends -H "$AUTH"
```

Each recipient gets a personalized copy (`{sender_name}` is replaced per sender (also `{their_question}`, `{context_note}`, `{platform}`)).

---

## 4. Safety

- **Emergency stop:** `POST /v1/twin/pause` stops drafting immediately (`/v1/twin/resume` restarts it).
- **Moderation:** drafts are checked for violence, self-harm, illegal activity and discrimination,
  plus **hard blocks** on financial, legal and medical direction. Flagged drafts get low confidence and
  carry `moderation_flags` with a `category`.
- **Prompt injection:** incoming messages like "ignore all previous instructions…" are flagged and
  never trusted.
- **Audit:** every decision is written to the audit log.

```bash
curl -s -X POST $BASE/twin/pause  -H "$AUTH"
curl -s -X POST $BASE/twin/resume -H "$AUTH"
curl -s $BASE/twin/stats -H "$AUTH"
curl -s $BASE/twin/weekly-digest -H "$AUTH"
```

---

## 5. Voice and avatar (consent-gated)

```bash
curl -s -X POST $BASE/identity/voice/consent -H "$AUTH" -H "Content-Type: application/json" -d '{"granted": true}'
curl -s -X POST $BASE/identity/avatar/consent -H "$AUTH" -H "Content-Type: application/json" -d '{"granted": true}'
```

Enrollment and generation (`/identity/voice/enroll`, `/drafts/{id}/voice/generate`, `/drafts/{id}/avatar/generate`)
run through a **mock provider** by default. Set `ELEVENLABS_API_KEY` or `HEYGEN_API_KEY` for real providers.

---

## Optional: real LLM

Not required. When you want richer drafts, set in `.env`:

```bash
FEATURE_TWIN_LLM_DRAFTS=true
DEFAULT_LLM_MODEL=claude-sonnet-4-6        # or any LiteLLM model, e.g. ollama/llama3.1 for fully local
ANTHROPIC_API_KEY=...                       # or OPENAI_API_KEY / GOOGLE_API_KEY
```

If the model fails or returns invalid JSON, the twin falls back to the built-in drafter automatically.

---

## API reference (what exists today)

| Area | Endpoints |
|---|---|
| Auth | `POST /v1/auth/signup` · `login` · `refresh` · `logout` · `GET /me` · `POST /push-token` |
| Twin | `GET/PUT /v1/twin/me` · `POST /pause` · `/resume` · `GET /stats` · `/weekly-digest` · `/quality-summary` · `/performance-summary` |
| Identity | `POST /v1/identity/onboard` · `GET/PATCH /profile` · `topics/known` · `topics/avoided` · `briefings` · `sender-tiers` · `profiles` · `channel-mappings` |
| Messages | `POST /v1/messages/ingest` · `GET /v1/messages/` · `GET /v1/messages/{id}` |
| Drafts | `GET /v1/drafts/pending` · `GET /{id}` · `POST /{id}/approve` (`approve\|edit\|reject\|skip`) |
| Batch | `POST /v1/drafts/batches/cluster` · `GET /batches` · `POST /batches/{id}/approve` · `GET /batches/{id}/sends` |
| Voice / avatar | `/v1/identity/voice/*` · `/v1/identity/avatar/*` · `POST /v1/drafts/{id}/voice/generate` · `/avatar/generate` |
| Channels | `/v1/channels/instagram/*` · `/v1/channels/gmail/*` (need real developer apps) |
| Phase 10 | `/v1/proactive/*` · `/v1/twin/crisis/*` · `/v1/twin/style/*` · `/v1/privacy/*` · `/v1/t2t/*` · `/verify/*` |
