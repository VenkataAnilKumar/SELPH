# SELPH — MVP Build Plan

> Version: 1.0
> Created: 2026-04-24
> Target: Content Creators (MVP Segment)

---

## Build Philosophy

Policy source of truth for autonomy, retention, and compliance controls:
- [SELPH_Canonical-Policy-Matrix.md](../04-safety/SELPH_Canonical-Policy-Matrix.md)

### Golden Rule
> Text first. Voice second. Avatar third.

Build the smallest thing that proves the core concept.
Layer complexity only after the core is validated.

### The One Question MVP Must Answer
> "Can the twin draft a response that sounds so much like the user —
>  they approve it without editing?"

If yes → product works. Everything else is polish.

### What We Are NOT Building in MVP
- Real-time video avatar calls
- Multi-language support
- Financial / legal actions
- Enterprise admin controls
- API for developers
- More than 2 channel integrations (Instagram DMs + Gmail only)
- Twitter/X, WhatsApp, Slack, Discord (Phase 2)
- Proactive Twin, Twin-to-Twin Protocol, On-Device Processing (Phase 2/3)

### Phase 1 Features Built Alongside MVP (Weeks 4–8)
These three features from the expansion plan are low-effort and must ship before channels go live:

1. **Twin Briefing** — user creates time-scoped context injected into every prompt. Prevents the twin sending wrong replies during campaigns. Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-2--twin-briefing--context-injection)
2. **VIP Override / Relationship Tiers** — sender-level routing control. VIP contacts bypass twin entirely. Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-4--vip-override--relationship-tiers)
3. **Batch Pattern Approval** — cluster similar messages, approve one template, twin personalizes all. Essential for high-volume creators. Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-1--batch-pattern-approval)

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python + FastAPI | Fast to build, async support, AI-friendly |
| Database | PostgreSQL + pgvector | Structured data + vector memory (on-DB, no external hop) |
| Vector Search | pgvector (on Railway PostgreSQL) | Similarity search co-located with identity data — no external service |
| LLM | LiteLLM Gateway (default: claude-sonnet-4-6; user-selectable: GPT-5, Gemini, DeepSeek, Llama, Mistral) | Multi-model, BYOK, cost tracking, automatic fallback |
| Local LLM | Ollama | Run any open model on-device at zero API cost |
| Voice Clone | Chatterbox (MIT, free, default) / ElevenLabs (paid, optional) | Open-source default saves cost; paid option for premium quality |
| Avatar Clone | Linly-Talker / Duix-Avatar (MIT, free, default) / HeyGen (paid, optional) | Open-source default; paid option for managed cloud quality |
| Queue | Redis + Celery | Async message processing for MVP |
| Real-time | WebSocket + Firebase FCM | WebSocket for active sessions, push for offline |
| Mobile App | React Native | iOS + Android from one codebase |
| Web App | Next.js 15 (App Router) | Browser-based twin dashboard + draft approval |
| Landing Page | Next.js 15 (static) | selph.ai marketing site — waitlist, pricing, docs |
| Auth | JWT (RS256) via FastAPI | Shared auth across mobile, web app, and landing page |
| Storage | Cloudflare R2 (S3-compatible, free 10GB) | Voice recordings, avatar videos — zero egress cost |
| Backend Hosting | Railway | Docker services + managed PostgreSQL + Redis |
| Frontend Hosting | Vercel (free tier) | Web app + landing page — auto-deploy from GitHub |

Full architecture: [SELPH_System-Architecture.md](../05-technical/SELPH_System-Architecture.md)

---

## Phase 0 — Foundation
**Duration:** Week 1–2
**Goal:** Skeleton that everything else plugs into

### What to Build
```
├── Project structure
│   ├── /backend          FastAPI app
│   ├── /mobile           React Native app
│   └── /worker           Celery async workers
│
├── Database Schema
│   ├── users             (id, name, email, created_at)
│   ├── twins             (user_id, style_profile, settings)
│   ├── messages          (twin_id, channel, content, status)
│   ├── drafts            (message_id, content, confidence, status)
│   └── audit_logs        (twin_id, action, timestamp, result)
│
├── Auth System
│   ├── Email + password signup
│   ├── JWT token auth
│   └── Identity verification placeholder (Phase 4 — required before channels go live)
│
└── Base API Routes
    ├── POST /auth/signup
    ├── POST /auth/login
    ├── GET  /twin/me
    └── POST /twin/pause
```

### Done When
- [ ] User can sign up and log in
- [ ] Database running with all tables
- [ ] API returns 200 on health check
- [ ] Mobile app shell loads and authenticates

---

## Phase 1 — Identity Core
**Duration:** Week 2–4
**Goal:** SELPH learns who the user is

### What to Build

#### 1.1 Onboarding Questionnaire
```
Questions asked at signup:
1. What do you do? (role / domain)
2. How would you describe your communication style?
   → Formal / Casual / Friendly / Direct / Humorous
3. What topics do you NOT talk about publicly?
4. What's your typical response length?
   → Short / Medium / Detailed
5. What tone do you use with fans/followers?
6. What are 3 words that describe you?
```

#### 1.2 Social Content Ingestion
```
Connect Instagram → pull last 500 captions + DM replies
Connect Twitter/X → pull last 500 tweets + replies
Connect Gmail     → pull last 200 sent emails (subject + body)

NLP Analysis on ingested content:
├── Vocabulary fingerprint (words you use often)
├── Sentence length patterns
├── Emoji usage patterns
├── Greeting and sign-off patterns
├── Response length preferences
└── Topic clusters (what you talk about)
```

#### 1.3 Identity Profile Storage
```python
# Stored in PostgreSQL (structured) + pgvector (embeddings co-located on same DB)

IdentityProfile:
  user_id: str
  domain: str                    # "content creator", "developer"
  tone: str                      # "casual, friendly, humorous"
  vocabulary: List[str]          # top 200 words/phrases they use
  avg_response_length: int       # words
  emoji_usage: float             # 0.0 to 1.0
  topics_known: List[str]        # topics they speak about
  topics_avoided: List[str]      # topics they never address
  greeting_style: str            # "Hey!", "Hi there", "Yo"
  sign_off_style: str            # "Love, X", "Cheers", none
  sample_responses: List[str]    # 20 real responses for few-shot
```

### Done When
- [ ] User completes onboarding questionnaire
- [ ] System ingests and analyzes their social content
- [ ] Identity profile stored and retrievable
- [ ] Profile visible to user in app ("This is how your twin sees you")

---

## Phase 2 — Twin Engine
**Duration:** Week 4–6
**Goal:** Twin drafts responses that sound like the user

### What to Build

#### 2.1 Message Intake
```
Incoming message received from channel
  ↓
Parsed and stored in messages table
  ↓
Queued for twin processing (Celery worker)
  ↓
Context retrieved:
  ├── User's identity profile
  ├── Last 5 interactions with this sender
  ├── Platform context (Instagram DM vs Email)
  └── Topic detected in incoming message
```

#### 2.2 Draft Generation (Claude API)

```python
# System prompt built dynamically per user

SYSTEM_PROMPT = f"""
You are the digital twin of {user.name}.

Your communication style:
- Tone: {profile.tone}
- Average response length: {profile.avg_response_length} words
- Emoji usage: {"frequent" if profile.emoji_usage > 0.5 else "minimal"}
- Greeting style: {profile.greeting_style}
- Topics you know well: {", ".join(profile.topics_known)}
- Topics you never discuss: {", ".join(profile.topics_avoided)}

Here are real examples of how {user.name} responds:
{format_examples(profile.sample_responses)}

RULES:
- Always respond exactly as {user.name} would
- Never claim to be an AI unless directly asked
- If unsure, say "Let me get back to you on that"
- Never discuss topics marked as avoided
- Match the energy and length of the incoming message
"""

USER_PROMPT = f"""
Incoming message from {sender_name} on {platform}:
"{incoming_message}"

Draft a response as {user.name}.
"""
```

#### 2.3 Confidence Scoring

```python
# After draft is generated, score confidence

def score_confidence(draft, profile, incoming_message) -> float:
    # pseudocode — implement in Phase 2
    factors = {
        "topic_known": topic_in_known_list(draft, profile),        # 0-1
        "length_match": length_within_range(draft, profile),       # 0-1
        "tone_match": tone_similarity(draft, profile),             # 0-1
        "no_avoided_topics": no_avoided_topics(draft, profile),    # 0-1
        "sample_similarity": similarity_to_samples(draft, profile) # 0-1
    }
    weights = [0.25, 0.15, 0.25, 0.20, 0.15]
    return sum(v * w for v, w in zip(factors.values(), weights))

# Thresholds
HIGH_CONFIDENCE   = 0.85+   → send to user as "Ready to send"
MEDIUM_CONFIDENCE = 0.65-0.84 → send to user as "Review suggested"
LOW_CONFIDENCE    = below 0.65 → send to user as "Needs your input"
```

#### 2.4 Draft Storage
```
Draft created
  ↓
Stored with:
  ├── draft content
  ├── confidence score
  ├── confidence label (high/medium/low)
  ├── status: pending_approval
  └── expires_at: 24 hours
```

### Done When
- [ ] Twin generates a draft for any incoming text message
- [ ] Draft sounds like the user (team tests with real profiles)
- [ ] Confidence score correctly identifies weak drafts
- [ ] Draft stored and retrievable via API

---

## Phase 3 — Approval Loop
**Duration:** Week 6–7
**Goal:** Human reviews and approves drafts in one tap

### What to Build

#### 3.1 Push Notification
```
Draft ready
  ↓
Firebase push notification sent to user's phone:

"[Sender name] messaged you on Instagram
 Your twin drafted a reply — tap to review"
```

#### 3.2 Mobile Approval Screen
```
┌─────────────────────────────┐
│ DM from @sarah_designs       │
│ "Love your content! Can you  │
│  share your editing setup?"  │
├─────────────────────────────┤
│ SELPH DRAFT          85% ✓  │
│                              │
│ "Hey Sarah! Thanks so much   │
│  🙏 I use Premiere Pro +     │
│  LUTS from my shop. Link     │
│  in bio! 🎬"                 │
├─────────────────────────────┤
│ [✓ SEND]  [✏ EDIT]  [✗ SKIP]│
└─────────────────────────────┘
```

#### 3.3 Feedback Loop
```
User approves  → draft sent, logged as "approved", twin learns +1
User edits     → edited version sent, diff stored, twin learns from edit
User rejects   → user asked "what was wrong?" → twin learns from reason
User skips     → no action, stored for later, no learning signal
```

#### 3.4 Twin Learning from Feedback
```python
# After every approval/edit/reject — update identity profile

def update_profile_from_feedback(draft, user_action, edited_version=None):
    if user_action == "approved":
        # Add draft to sample_responses pool
        # Reinforce current style settings

    elif user_action == "edited":
        # Compare original vs edited
        # Extract what changed (length, tone, words, emoji)
        # Adjust profile weights accordingly

    elif user_action == "rejected":
        # Store rejection reason
        # Reduce weight of detected style mismatch
```

### Done When
- [ ] Push notification delivered within 5 seconds of draft ready
- [ ] User can approve in one tap
- [ ] User can edit inline before sending
- [ ] Twin profile updates after every feedback signal
- [ ] Approval rate tracked as primary metric

---

## Phase 4 — Safety Layer
**Duration:** Week 7–8
**Goal:** SELPH SAFE framework fully operational BEFORE channels go live

> ⚠️ Safety must be built before any real user data flows through channels.
> This phase was intentionally moved ahead of channel integration.

### What to Build

#### 4.1 Content Moderation
```python
# Before any draft is sent to user for approval
# Check for policy violations

def moderate_draft(draft) -> ModerationResult:
    checks = [
        check_harmful_content(draft),      # violence, hate speech
        check_financial_advice(draft),      # blocked by default
        check_legal_advice(draft),          # blocked by default
        check_medical_advice(draft),        # blocked by default
        check_impersonation_risk(draft),    # claiming to be someone else
    ]
    return ModerationResult(passed=all(checks), flags=failed_checks)
```

#### 4.2 Digital Watermarking
```
All twin-generated text:
→ Invisible Unicode watermark embedded
→ Traceable to SELPH account ID + timestamp

All twin-generated audio (Phase 6):
→ ElevenLabs watermark (built-in)
→ Additional SELPH audio watermark layer

All twin-generated video (Phase 7):
→ HeyGen watermark (built-in)
→ Invisible pixel-level SELPH watermark
```

#### 4.3 Audit Log
```
Every twin action logged:
├── timestamp
├── channel
├── sender
├── incoming message (hashed)
├── draft generated (hashed)
├── confidence score
├── user action (approved/edited/rejected)
├── final message sent (hashed)
└── twin_version (profile snapshot ID)

Retention: 2 years minimum (anonymize where required by policy)
User access: full via dashboard
Export: CSV available on request
```

#### 4.4 Anomaly Detection
```python
# Run after every 10 twin actions

def detect_anomalies(twin_id) -> List[Anomaly]:
    checks = [
        unusual_message_volume(twin_id),     # 10x normal rate
        unusual_topics(twin_id),             # topics never discussed before
        unusual_send_time(twin_id),          # 3am activity
        low_approval_rate_spike(twin_id),    # approval rate drops below 40%
    ]
    # Any anomaly → pause twin + alert user
```

### Done When
- [ ] All drafts pass moderation before reaching user
- [ ] Watermark embedded in all text outputs
- [ ] Audit log captures every action
- [ ] Anomaly detection pauses twin and alerts user

---

## Phase 5 — Channel Integration
**Duration:** Week 8–10
**Goal:** Twin works on real channels (Instagram DMs + Gmail)

### What to Build

#### 5.1 Instagram Integration
```
User connects Instagram Business Account
  ↓
Onboarding guides personal-account users to upgrade to Business Account
  ↓
Webhook registered for incoming DMs
  ↓
New DM arrives → sent to twin engine
  ↓
Draft approved by user
  ↓
Reply sent via Instagram Graph API
```

Key API: Instagram Messaging API (requires Instagram Business Account)
Note: Guide users through Business Account setup in onboarding — this is a known friction point.

#### 5.2 Gmail Integration
```
User connects Gmail via OAuth
  ↓
Gmail watch() registered → Google Pub/Sub push notifications
  ↓
New email arrives → Pub/Sub pushes to SELPH webhook (real-time, not polling)
  ↓
Email → twin engine → draft
  ↓
User approves
  ↓
Reply sent via Gmail API as user
```

Key API: Gmail Push Notifications via Google Cloud Pub/Sub (NOT polling — polling is slow and wastes quota)

#### 5.3 Channel Router
```python
# Each channel has its own style context

CHANNEL_CONTEXT = {
    "instagram_dm": {
        "style_hint": "casual, short, emoji-friendly",
        "max_length": 150,
        "format": "plain text"
    },
    "gmail": {
        "style_hint": "professional, structured",
        "max_length": 300,
        "format": "with greeting and sign-off"
    }
}
```

### Done When
- [ ] Instagram DMs received and processed automatically
- [ ] Gmail emails received via Pub/Sub push (not polling)
- [ ] Replies sent successfully through each channel
- [ ] User can connect/disconnect channels from settings
- [ ] All channel traffic passes through Safety Layer (Phase 4)

### What to Build

#### 5.1 Instagram Integration
```
User connects Instagram Business Account
  ↓
Onboarding guides personal-account users to upgrade to Business Account
  ↓
Webhook registered for incoming DMs (Channel Adapter layer)
  ↓
New DM arrives → normalized MessageReceived event → twin engine
  ↓
Draft approved by user
  ↓
Reply sent via Instagram Graph API
```

Key API: Instagram Messaging API (requires Instagram Business Account)
Note: Guide users through Business Account setup in onboarding — this is a known friction point.

#### 5.2 Gmail Integration
```
User connects Gmail via OAuth
  ↓
Gmail watch() registered → Google Pub/Sub push notifications
  ↓
New email arrives → Pub/Sub pushes to SELPH webhook (real-time, not polling)
  ↓
Email → Channel Adapter → twin engine → draft
  ↓
User approves
  ↓
Reply sent via Gmail API as user
```

Key API: Gmail Push Notifications via Google Cloud Pub/Sub (NOT polling)

#### 5.3 Channel Router
```python
CHANNEL_CONTEXT = {
    "instagram_dm": {
        "style_hint": "casual, short, emoji-friendly",
        "max_length": 150,
        "format": "plain text"
    },
    "gmail": {
        "style_hint": "professional, structured",
        "max_length": 300,
        "format": "with greeting and sign-off"
    }
}
```

#### 5.4 Infrastructure Readiness — Railway Production

Before channels go live, verify Railway production environment is fully configured:
- FastAPI + Celery services deployed as Docker containers on Railway
- Railway managed PostgreSQL (production plan) in use
- Railway managed Redis in use
- Cloudflare R2 bucket created and credentials set in Railway env vars
- Cloudflare DNS pointing selph.ai to Railway domain
- Cloudflare WAF enabled on production domain
- All secrets stored as Railway environment variables (not in code)

### Done When
- [ ] Instagram DMs received and processed automatically
- [ ] Gmail emails received via Pub/Sub push (not polling)
- [ ] Replies sent successfully through each channel
- [ ] User can connect/disconnect channels from settings
- [ ] All channel traffic passes through Safety Layer (Phase 4)
- [ ] Railway production environment fully configured before first real user

---

## Phase 6 — Voice Clone
**Duration:** Week 10–12
**Goal:** Twin responds in user's actual voice

### What to Build

#### 6.1 Voice Recording Flow (Mobile)
```
User opens "Voice Setup"
  ↓
Prompted to read 25-30 sentences aloud (2-3 min total at ~150 words/min)
  ↓
Audio uploaded to Cloudflare R2
  ↓
Default: Sent to Chatterbox (self-hosted) → voice model created (MIT, free)
Optional: Sent to ElevenLabs API → voice model created (paid, premium quality)
  ↓
Voice model ID + provider stored in user profile
  ↓
Test playback: user hears their cloned voice
  ↓
Approve or re-record
```

#### 6.2 Voice Response Generation
```python
# When user approves a draft that needs audio response
# Provider is determined by user's voice settings (default: Chatterbox)

def generate_voice_response(draft_text, user_voice_model_id, provider="chatterbox") -> AudioFile:
    if provider == "chatterbox":
        # Self-hosted Chatterbox (MIT, free)
        response = chatterbox_client.synthesize(
            text=draft_text,
            voice_id=user_voice_model_id,
            model="chatterbox-tts-1"
        )
    elif provider == "elevenlabs":
        # Optional paid premium integration
        response = elevenlabs.generate(
            text=draft_text,
            voice=user_voice_model_id,
            model="eleven_multilingual_v2",
            settings=VoiceSettings(stability=0.7, similarity_boost=0.85)
        )
    return apply_selph_watermark(response)
```

#### 6.3 When Voice is Used
- User explicitly requests voice response
- Channel supports audio (WhatsApp voice notes, future)
- Video avatar response (Phase 7)

### Done When
- [ ] User records voice in under 5 minutes
- [ ] Chatterbox voice model created successfully (default path)
- [ ] Generated audio sounds like user (user-rated 4+/5)
- [ ] Audio watermarked before delivery
- [ ] ElevenLabs integration available as opt-in premium setting

---

## Phase 7 — Avatar Clone
**Duration:** Week 12–14
**Goal:** Twin responds as a video of the user

### What to Build

#### 7.1 Avatar Recording Flow (Mobile)
```
User opens "Avatar Setup"
  ↓
Instructed to record 60-second neutral video:
  ├── Good lighting
  ├── Face centered
  ├── Neutral expression
  └── Multiple angles (optional for quality)
  ↓
Video uploaded to Cloudflare R2
  ↓
Default: Sent to Linly-Talker (self-hosted, MIT) → avatar model created (free)
Optional: Sent to HeyGen API → avatar model created (paid, premium quality)
  ↓
Preview generated: 10-second test video
  ↓
User approves or re-records
```

#### 7.2 Video Response Generation
```python
# When video response requested
# Provider determined by user's avatar settings (default: Linly-Talker)

def generate_avatar_response(draft_text, user_avatar_id, user_voice_id, provider="linly"):
    if provider == "linly":
        # Self-hosted Linly-Talker (MIT, free)
        video = linly_client.generate(
            avatar_id=user_avatar_id,
            voice_id=user_voice_id,
            script=draft_text,
            resolution="1080p"
        )
    elif provider == "heygen":
        # Optional paid premium integration
        video = heygen.create_video(
            avatar_id=user_avatar_id,
            voice_id=user_voice_id,
            script=draft_text,
            background="clean_white",
            resolution="1080p"
        )
    return apply_selph_watermark_video(video)
```

#### 7.3 Transparent Mode Overlay
```
In Transparent Mode:
Bottom of every video shows:
"[Name]'s SELPH Digital Twin — verify at selph.ai/verify/[id]"
```

### Done When
- [ ] User records avatar in under 5 minutes
- [ ] Linly-Talker avatar model created successfully (default path)
- [ ] Generated video looks and sounds like user
- [ ] Transparent mode overlay applied correctly
- [ ] HeyGen integration available as opt-in premium setting

---

## Phase 8 — Polish & Beta Launch
**Duration:** Week 14–16
**Goal:** Ship to 50 beta creators, gather feedback, iterate

### What to Build
- [ ] Onboarding flow polish (reduce drop-off)
- [ ] Twin quality dashboard ("Your twin's approval rate: 84%")
- [ ] Weekly digest email ("Your twin handled 47 messages this week")
- [ ] Referral system ("Invite a creator, get 1 month free")
- [ ] Bug fixes from beta feedback
- [ ] Performance optimization (draft generation <10 seconds)

---

## Build Order Summary

```
Week 1-2   ████░░░░░░░░░░░░  Phase 0: Foundation
Week 2-4   ████████░░░░░░░░  Phase 1: Identity Core
Week 4-6   ████████████░░░░  Phase 2: Twin Engine
Week 6-7   ██████████████░░  Phase 3: Approval Loop
Week 7-8   ████░░░░░░░░░░░░  Phase 4: Safety Layer  ← BEFORE channels
Week 8-10  ████████░░░░░░░░  Phase 5: Channel Integration
Week 10-12 ████████████░░░░  Phase 6: Voice Clone
Week 12-14 ██████████████░░  Phase 7: Avatar Clone
Week 14-16 ████████████████  Phase 8: Beta Launch
```

**Total: 16 weeks to full MVP**
**Minimum Viable Demo: 6 weeks (Phases 0-3)**

---

## Milestone Gates

| Milestone | Week | Gate Criteria |
|---|---|---|
| **Demo Ready** | Week 6 | Twin drafts text responses, human approves in app |
| **Safety Live** | Week 8 | Moderation, audit, watermark, anomaly detection active |
| **Alpha** | Week 10 | Instagram + Gmail live, safety layer protecting all traffic |
| **Voice MVP** | Week 12 | Twin responds in user's voice |
| **Full MVP** | Week 14 | Voice + avatar + 2 channels + safety |
| **Beta Launch** | Week 16 | 50 creators onboarded, feedback collected |

---

## Team Needed

| Role | Phase | Responsibility |
|---|---|---|
| AI Engineer | 1-8 | Twin engine, Claude integration, identity profile |
| Backend Engineer | 0-5 | FastAPI, database, channel integrations |
| Mobile Engineer | 0-4 | React Native app, approval interface |
| ML Engineer | 1-3 | Style analysis, confidence scoring, learning loop |
| DevOps | 0-8 | Infra, deployment, monitoring |

**Solo builder path:** Phases 0-3 achievable alone in 8 weeks using Claude API + hosted services.

---

## First Day Action Items

If starting tomorrow:

```
Day 1:
1. Create GitHub repo: selph-ai
2. Set up FastAPI project structure
3. Create PostgreSQL database (Supabase)
4. Set up React Native project
5. Get API keys: Claude (default LLM), Firebase; Install LiteLLM; Install Chatterbox + Linly-Talker (self-hosted, free)

Day 2-3:
6. Build auth (signup, login, JWT)
7. Build database schema (all tables)
8. Build base API routes

Day 4-5:
9. Start onboarding questionnaire UI
10. Build identity profile data model

Week 2:
11. Instagram content ingestion
12. NLP style analysis pipeline
13. Identity profile storage (PostgreSQL + pgvector embeddings)
```

---

## Success Criteria for MVP

| Metric | Target |
|---|---|
| Twin Approval Rate | >80% approved without editing |
| Draft Generation Speed | <10 seconds |
| User Setup Time | <15 minutes to active twin |
| Weekly Active Rate | >70% of beta users active weekly |
| NPS Score | >50 from beta creators |

---

*Status: MVP Build Plan v1.0 — Ready to Execute*
