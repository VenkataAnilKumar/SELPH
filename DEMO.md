# SELPH — Live Demo Walkthrough

> **The complete end-to-end demo of SELPH in action.**
> From zero to a working digital twin that drafts replies in your voice, manages your VIPs, handles batches, and gets smarter with every approval.

---

## Prerequisites

```bash
# Clone and start
git clone https://github.com/VenkataAnilKumar/selph.git
cd selph
cp .env.example .env
# Add ANTHROPIC_API_KEY (or any LiteLLM-supported key) to .env
docker compose up --build

# API: http://localhost:8000
# Docs: http://localhost:8000/docs  ← interactive, try endpoints here too
```

Set a shell variable for convenience:
```bash
BASE="http://localhost:8000/v1"
```

---

## Act 1 — Creating Your Twin

### Step 1: Register

```bash
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maya@example.com",
    "password": "strongpassword",
    "full_name": "Maya Chen"
  }'
```

```json
{
  "id": "usr_01HZ...",
  "email": "maya@example.com",
  "full_name": "Maya Chen",
  "created_at": "2026-04-28T09:00:00Z"
}
```

---

### Step 2: Login and Get Your Token

```bash
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "maya@example.com", "password": "strongpassword"}' \
  | jq -r .access_token)

echo "Token: $TOKEN"
```

All subsequent calls use `-H "Authorization: Bearer $TOKEN"`.

---

### Step 3: Complete Your Onboarding — This Is Where Your Twin Begins

```bash
curl -s -X POST $BASE/identity/onboard \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "tech entrepreneur and content creator",
    "tone": "warm",
    "formality": 3,
    "communication_style": "storytelling",
    "audience_tone": "community feel",
    "three_words": ["authentic", "direct", "curious"],
    "response_length": "medium",
    "topics_avoided": ["politics", "religion"],
    "greeting_style": "Hey!",
    "sign_off_style": "Talk soon,"
  }'
```

```json
{
  "twin": {
    "id": "twn_01HZ...",
    "domain": "tech entrepreneur and content creator",
    "tone": "warm",
    "formality": 3,
    "status": "active"
  },
  "identity_profile": {
    "vocabulary_description": "authentic, direct, curious",
    "communication_style": "storytelling; audience tone: community feel",
    "topics_avoided": ["politics", "religion"],
    "greeting_style": "Hey!",
    "sign_off_style": "Talk soon,"
  }
}
```

Your twin now knows how you write. Every draft will reflect this.

---

### Step 4: Add Topics Your Twin Knows You're an Expert In

```bash
curl -s -X POST $BASE/identity/topics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI product development",
    "description": "Building AI-first products, LLM stacks, agentic systems",
    "confidence_level": 5,
    "is_active": true
  }'

curl -s -X POST $BASE/identity/topics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "creator economy",
    "description": "Monetization, audience growth, community building",
    "confidence_level": 4,
    "is_active": true
  }'
```

Your twin now knows your domain expertise depth per topic.

---

## Act 2 — Giving Your Twin Real-Time Intelligence

### Step 5: Set a Twin Briefing

You're speaking at a conference. Tell your twin:

```bash
curl -s -X POST $BASE/identity/briefings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "availability",
    "content": "I am at TechConf 2026 this week. Keep replies short — 2-3 sentences max. Offer a follow-up call for anything detailed.",
    "expires_at": "2026-05-03T23:59:59Z"
  }'
```

```json
{
  "id": "brf_01HZ...",
  "type": "availability",
  "content": "I am at TechConf 2026 this week...",
  "is_active": true,
  "expires_at": "2026-05-03T23:59:59Z"
}
```

Every draft your twin generates until May 3rd will be short and offer a follow-up call — automatically.

---

### Step 6: Set Up VIP Sender Tiers

Your co-founder's messages should never touch the twin:

```bash
curl -s -X POST $BASE/identity/sender-tiers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "james@cofounder.com",
    "sender_channel": "gmail",
    "tier": 0,
    "label": "Co-founder James",
    "reason": "All messages route directly to me"
  }'
```

Your investor gets Tier 1 — twin drafts, but you always review:

```bash
curl -s -X POST $BASE/identity/sender-tiers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "partner@vcfirm.com",
    "sender_channel": "gmail",
    "tier": 1,
    "label": "Lead Investor",
    "reason": "Always review before sending"
  }'
```

---

## Act 3 — Your Twin in Action

### Step 7: Ingest an Incoming Message

A fan slides into your Instagram DMs:

```bash
curl -s -X POST $BASE/messages/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "instagram_dm",
    "sender_id": "fan_@techgirl2026",
    "content": "Hey Maya! Your talk on agentic AI blew my mind. How do you stay ahead of what'\''s happening in AI without getting overwhelmed?",
    "metadata": {
      "platform": "instagram",
      "message_id": "ig_msg_77291"
    }
  }'
```

```json
{
  "message_id": "msg_01HZ...",
  "status": "queued",
  "twin_status": "processing",
  "estimated_draft_seconds": 8
}
```

The Twin Engine is running:
- Loaded your identity model (tone: warm, domain: AI + creator economy)
- Loaded your active briefing (conference week, keep it short)
- Checking sender tier (fan → Standard tier, normal flow)
- Building the prompt with your vocabulary and style
- Generating the draft via Claude Sonnet

---

### Step 8: Review Your Twin's Draft

```bash
curl -s $BASE/drafts?status=pending_approval \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "total": 1,
  "items": [
    {
      "id": "dft_01HZ...",
      "message_id": "msg_01HZ...",
      "channel": "instagram_dm",
      "sender_id": "fan_@techgirl2026",
      "original_message": "Hey Maya! Your talk on agentic AI blew my mind...",
      "draft_content": "Hey! So glad the talk landed well 😊 Honestly — I stopped trying to consume everything. I pick 2-3 people whose thinking I trust and just follow them closely. Less noise, more signal. Happy to share who those are over a proper call next week if you want to go deeper!",
      "confidence_score": 0.91,
      "generation_source": "twin_engine",
      "llm_model": "claude-sonnet-4-6",
      "estimated_cost_usd": 0.00042,
      "status": "pending_approval",
      "briefings_applied": ["brf_01HZ..."],
      "word_count": 52,
      "created_at": "2026-04-28T09:03:47Z"
    }
  ]
}
```

**91% confidence.** The twin knew to keep it short (briefing), warm (your tone), offer a call (briefing), and reference the talk topic (context). This sounds like Maya.

---

### Step 9: Approve It

```bash
curl -s -X POST $BASE/drafts/dft_01HZ.../approve \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "dft_01HZ...",
  "status": "approved",
  "user_action": "approved",
  "sent_at": "2026-04-28T09:04:12Z"
}
```

Reply sent. Fan got a personal response in Maya's voice. Maya spent 3 seconds.

The twin logs this approval. Confidence in this message pattern goes up. Next time: faster, better.

---

### Step 10: Reject and Teach Your Twin

A different draft comes in — your twin got the tone slightly off:

```bash
curl -s -X POST $BASE/drafts/dft_01HZ_2.../reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Too formal. I never use words like '\''subsequently'\'' with fans. Keep it casual."
  }'
```

```json
{
  "id": "dft_01HZ_2...",
  "status": "rejected",
  "user_action": "rejected",
  "rejection_reason": "Too formal. I never use words like 'subsequently' with fans.",
  "twin_learned": true
}
```

The rejection reason is vectorized and stored. The next draft won't make this mistake.

---

## Act 4 — Scale: Batch Pattern Approval

### Step 11: Creator-Scale — 50 DMs About the Same Thing

Your latest YouTube video went viral. 50 people asked the same question.

**Cluster them:**

```bash
curl -s -X POST $BASE/drafts/batches/cluster \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min_cluster_size": 3,
    "channel": "instagram_dm"
  }'
```

```json
{
  "total": 2,
  "items": [
    {
      "id": "cls_01HZ...",
      "topic_summary": "Asking about recommended resources for learning agentic AI",
      "message_count": 47,
      "representative_message": "Hey! What resources would you recommend for getting started with agentic AI?",
      "status": "pending_approval"
    },
    {
      "id": "cls_01HZ_2...",
      "topic_summary": "Asking about the tech stack used in the demo",
      "message_count": 12,
      "representative_message": "What stack did you use for that digital twin demo?",
      "status": "pending_approval"
    }
  ]
}
```

**Approve the first cluster — 47 personalized replies in one request:**

```bash
curl -s -X POST $BASE/drafts/batches/cls_01HZ.../approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_override": null,
    "excluded_sender_ids": ["vip_@mentor_handle"]
  }'
```

```json
{
  "id": "bsn_01HZ...",
  "cluster_id": "cls_01HZ...",
  "messages_sent": 46,
  "messages_excluded": 1,
  "template_used": "Hey! Great question 😊 My go-to starting point right now is [personalized based on their profile]. If you want to go deeper — happy to chat next week. Talk soon,",
  "status": "sent",
  "audit_log_ids": ["alog_01...", "alog_02...", "..."]
}
```

**46 fans** got a personalized reply that sounds exactly like Maya wrote it just for them.
**Maya spent 8 seconds total.**

---

## Act 5 — Voice & Avatar

### Step 12: Consent to Voice Cloning

```bash
curl -s -X POST $BASE/identity/voice/consent \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consent_given": true,
    "provider": "chatterbox",
    "consent_text": "I consent to voice cloning using Chatterbox for SELPH twin responses."
  }'
```

### Step 13: Enroll Your Voice

```bash
curl -s -X POST $BASE/identity/voice/enroll \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "chatterbox",
    "sample_audio_url": "https://r2.selph.ai/voice-samples/maya_sample.wav",
    "duration_seconds": 90
  }'
```

```json
{
  "enrollment_id": "ven_01HZ...",
  "provider": "chatterbox",
  "status": "processing",
  "estimated_seconds": 45
}
```

### Step 14: Generate a Voice Response for a Draft

```bash
curl -s -X POST $BASE/drafts/dft_01HZ.../voice/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "chatterbox",
    "style": "conversational"
  }'
```

```json
{
  "task_id": "tsk_01HZ...",
  "status": "queued",
  "estimated_seconds": 8
}
```

```bash
# Poll for completion
curl -s $BASE/drafts/dft_01HZ.../voice/status \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "task_id": "tsk_01HZ...",
  "status": "complete",
  "audio_url": "https://r2.selph.ai/voice/maya_reply_01HZ.mp3",
  "duration_seconds": 12.4,
  "provider": "chatterbox"
}
```

Maya's reply — in Maya's voice. Synthesized in 8 seconds. At zero API cost (Chatterbox is MIT).

---

## Act 6 — Your Twin's Performance

### Step 15: Check Your Twin Stats

```bash
curl -s $BASE/twin/me \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "twn_01HZ...",
  "domain": "tech entrepreneur and content creator",
  "tone": "warm",
  "status": "active",
  "trust_stage": 2,
  "total_drafts_generated": 124,
  "approval_rate": 0.88,
  "avg_confidence_score": 0.89,
  "messages_handled_autonomously": 31
}
```

**88% approval rate.** Maya approves 88 out of every 100 drafts without editing. Her twin sounds like her.

---

### Step 16: Weekly Digest

```bash
curl -s $BASE/twin/weekly-digest \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "period_start": "2026-04-21",
  "period_end": "2026-04-28",
  "total_messages_received": 203,
  "drafts_generated": 198,
  "approved_without_edit": 162,
  "approved_with_edit": 24,
  "rejected": 12,
  "approval_rate": 0.88,
  "avg_time_to_approve_seconds": 4.1,
  "batch_sends": 3,
  "batch_messages_sent": 109,
  "voice_responses_generated": 8,
  "estimated_time_saved_hours": 6.3,
  "top_topics": ["agentic AI", "creator economy", "conference follow-ups"]
}
```

**6.3 hours saved this week.** Maya spent under a minute total on 203 messages.

---

### Step 17: Pause Your Twin Instantly

Going on stage? Pause the twin:

```bash
curl -s -X POST $BASE/twin/pause \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "twn_01HZ...",
  "status": "paused",
  "paused_at": "2026-04-28T14:00:00Z"
}
```

Resume after your talk:

```bash
curl -s -X POST $BASE/twin/resume \
  -H "Authorization: Bearer $TOKEN"
```

Emergency stop is also on the mobile app home screen — one tap.

---

## What You Just Saw

```
✅ Registered and logged in
✅ Completed onboarding → twin knows your voice and domain
✅ Added expert topics → twin knows what you know
✅ Set a Twin Briefing → real-time context injected into every draft
✅ Configured VIP tiers → your co-founder bypasses the twin
✅ Ingested an Instagram DM → twin drafted in your voice in 8 seconds
✅ Approved the draft → fan got a personal reply, twin learned
✅ Rejected a draft → taught the twin what you don't sound like
✅ Ran Batch Pattern Approval → 46 fans replied to in one tap
✅ Enrolled voice clone → synthesized audio reply in your voice
✅ Checked twin stats → 88% approval rate, 6.3 hours saved this week
✅ Paused and resumed the twin → emergency control always available
```

---

## Interactive API Explorer

All endpoints above are available at **http://localhost:8000/docs** with a full Swagger UI — try them live, see request/response schemas, authenticate with your JWT, and watch the system respond in real time.

---

## Full Feature Map

| Feature | Endpoint |
|---|---|
| Register / Login | `POST /v1/auth/register` · `POST /v1/auth/login` |
| Onboarding | `POST /v1/identity/onboard` |
| Topics | `POST/GET /v1/identity/topics` |
| Twin Profile | `GET /v1/twin/me` · `PATCH /v1/twin/me` |
| Twin Pause/Resume | `POST /v1/twin/pause` · `POST /v1/twin/resume` |
| Twin Briefings | `POST/GET /v1/identity/briefings` |
| VIP Sender Tiers | `POST/GET /v1/identity/sender-tiers` |
| Message Ingestion | `POST /v1/messages/ingest` |
| Draft Review | `GET /v1/drafts` |
| Draft Approve | `POST /v1/drafts/{id}/approve` |
| Draft Edit + Approve | `POST /v1/drafts/{id}/edit-approve` |
| Draft Reject | `POST /v1/drafts/{id}/reject` |
| Batch Cluster | `POST /v1/drafts/batches/cluster` |
| Batch Approve | `POST /v1/drafts/batches/{id}/approve` |
| Voice Consent | `POST /v1/identity/voice/consent` |
| Voice Enroll | `POST /v1/identity/voice/enroll` |
| Voice Generate | `POST /v1/drafts/{id}/voice/generate` |
| Avatar Consent | `POST /v1/identity/avatar/consent` |
| Avatar Enroll | `POST /v1/identity/avatar/enroll` |
| Avatar Generate | `POST /v1/drafts/{id}/avatar/generate` |
| Channel Connect | `POST /v1/channels/{channel}/connect` |
| Weekly Digest | `GET /v1/twin/weekly-digest` |
| Performance Summary | `GET /v1/twin/performance-summary` |
| Quality Summary | `GET /v1/twin/quality-summary` |
| Referral Program | `POST /v1/referrals/invite` |
| Health Check | `GET /health` · `GET /health/ready` |

Full API contract: [docs/05-technical/SELPH_API-Design.md](docs/05-technical/SELPH_API-Design.md)

---

## Next: Connect a Real Channel

Once your twin is working locally, connect a live channel:

### Gmail
```bash
curl -s -X POST $BASE/channels/gmail/connect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "https://app.selph.ai/channels/gmail/callback"}'
# Returns OAuth URL → user authenticates → Gmail webhooks live
```

### Instagram DMs
```bash
curl -s -X POST $BASE/channels/instagram/connect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instagram_business_account_id": "17841...", "redirect_uri": "..."}'
# Requires Instagram Business Account
# Returns OAuth URL → user authenticates → DMs flow into your twin
```

Setup guides: [docs/05-technical/SELPH_System-Architecture.md](docs/05-technical/SELPH_System-Architecture.md)

---

<div align="center">

**[← Back to README](README.md)**

*SELPH Demo — All 9 phases. One twin. Your voice.*

</div>
