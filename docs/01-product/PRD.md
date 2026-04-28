# SELPH — Product Requirements Document (PRD)

> Version: 1.0
> Created: 2026-04-24
> Status: Draft

---

## 1. Overview

### Product Name
**SELPH** — Your Digital Self

### Tagline
*"Be everywhere. Be SELPH."*

### One-Line Description
A universal Digital Twin AI that learns your voice, avatar, identity, and expertise — then acts on your behalf across any domain, for any person.

### Problem Statement
Everyone is overwhelmed by the volume of interactions, decisions, and tasks they face daily. Generic AI assistants help, but they don't sound like you, think like you, or represent you. SELPH is not an assistant — it IS you, available 24/7.

### Policy Source of Truth
Policy conflicts and final enforceable values are defined in:
- [SELPH_Canonical-Policy-Matrix.md](../04-safety/SELPH_Canonical-Policy-Matrix.md)

---

## 2. Goals & Success Metrics

### Business Goals
- Demo ready (text-only twin) in 6 weeks
- Full MVP (voice + avatar + 2 channels) in 16 weeks
- Reach 1,000 active twins by Month 5
- Reach 10,000 active twins by Month 9
- $50K MRR by Month 9

### Product Goals
- Twin accuracy: users approve >80% of drafts without editing
- Response time: twin drafts ready within 10 seconds
- Trust score: >4.5/5 average user satisfaction with twin quality
- Retention: >70% of users active after 30 days

### North Star Metric
**Twin Approval Rate** — % of twin-drafted responses approved by user without edits.
Higher = twin sounds more like the user = better product.

---

## 3. Target Users

### Primary (MVP)
**Content Creators & Influencers**
- Pain: Millions of DMs and comments, zero time to respond personally
- Goal: Engage fans at scale in their authentic voice
- Platforms: Instagram, YouTube, TikTok, Twitter/X
- Willingness to pay: High ($29–$99/month)

### Secondary (Post-MVP)
| Segment | Core Pain | Key Integration |
|---|---|---|
| Consultants / Freelancers | Repeating same answers to clients | Email, WhatsApp |
| Developers | GitHub issues, code reviews | GitHub, Slack, Discord |
| Executives | Email overload, meeting prep | Gmail, Outlook, Calendar |
| General Public | Want to be in two places at once | Any channel |

---

## 4. User Stories

### Identity Setup
- As a user, I can record my voice so SELPH can clone it
- As a user, I can record a short video so SELPH can create my avatar
- As a user, I can connect my social accounts and files so SELPH learns my style
- As a user, I can answer onboarding questions to define my personality and values
- As a user, I can verify my identity with government ID so my twin is authenticated

### Model Selection
- As a user, I can choose my preferred AI model (Claude, GPT-5, Gemini, DeepSeek, Llama, Mistral)
- As a user, I can bring my own API key for my chosen model (BYOK)
- As a user, I can run SELPH with a local model via Ollama at zero API cost
- As a user, my model choice is saved per profile and can be changed at any time
- As a user, I can see estimated cost per interaction for my chosen model

### Twin Operation
- As a user, I receive a notification when my twin has drafted a response for me
- As a user, I can approve, edit, or reject any draft in one tap
- As a user, I can set which types of messages my twin handles automatically
- As a user, I can pause my twin instantly at any time
- As a user, I can view a full audit log of everything my twin has done

### Twin Quality
- As a user, I can rate my twin's drafts to improve its accuracy
- As a user, I do a weekly calibration where I review 5 sample responses
- As a user, I can see my twin's confidence score on each draft
- As a user, low-confidence drafts are always sent to me for review

### Transparency & Trust
- As a recipient, I can see when I am talking to someone's SELPH twin
- As a recipient, I can verify a twin's authenticity via a verification link
- As a user, I can choose between Transparent Mode and Private Mode per conversation
- As a user, all twin outputs are watermarked for traceability

### Safety & Control
- As a user, financial and legal actions are blocked by default
- As a user, I can set hard limits on what my twin can and cannot do
- As a user, I am immediately alerted if anomalous twin behavior is detected
- As a platform, I can report a twin misusing someone's identity

---

## 5. Features

### Core Features (MVP)

#### 5.1 Identity Capture (MVP — Text Only)
- **Style Learning:** Connect Instagram, Twitter, email → NLP analysis of writing style
- **Personality Profile:** Onboarding questionnaire (tone, values, expertise, communication style)
- **Identity Verification:** Government ID + face match at signup
- **Voice Clone:** *(Phase 6 — Week 10-12)* Record 25-30 sentences → Chatterbox (MIT, free, default) / ElevenLabs (paid, optional)
- **Avatar Clone:** *(Phase 7 — Week 12-14)* Record 60-second video → Linly-Talker / Duix-Avatar (MIT, free, default) / HeyGen (paid, optional)

#### 5.2 Twin Engine
- Analyzes incoming messages and tasks
- Drafts responses in user's voice using their style model
- Generates video/audio responses using voice + avatar clone
- Assigns confidence score to every draft
- Escalates low-confidence drafts to human immediately

#### 5.3 Human-in-the-Loop Interface
- Mobile app notification with draft preview
- One-tap: Approve / Edit / Reject
- Edit mode: modify draft before sending
- Reject + reason → twin learns what was wrong
- Emergency pause button on home screen

#### 5.4 Operating Modes
- **Transparent Mode:** Recipients see "Powered by SELPH — [Name]'s Digital Twin"
- **Private Mode:** Twin drafts invisibly, user sends as themselves
- Mode selectable per conversation or per channel

#### 5.5 Audit & Safety
- Full audit log of all twin actions
- Weekly activity summary digest
- Content moderation on all outputs
- Invisible watermarking on all twin-generated content
- Anomaly detection with auto-pause

#### 5.6 Integrations (MVP)
- Instagram DMs *(requires Instagram Business Account — onboarding must guide users)*
- Email (Gmail via OAuth + Push Notifications)

#### 5.7 Post-MVP Integrations (Phase 2)
- Twitter/X mentions and DMs
- WhatsApp (via Meta Business API — requires approval, non-trivial)
- Slack / Discord
- GitHub

#### 5.8 Batch Pattern Approval *(Phase 1 — alongside MVP)*
- Semantic clustering of similar incoming messages
- One template approval covers N personalized replies
- User reviews cluster summary before approving
- Per-sender exclusion from a batch
- Full audit log per batch send
- Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-1--batch-pattern-approval)

#### 5.9 Twin Briefing / Context Injection *(Phase 1 — alongside MVP)*
- User creates time-scoped facts, opinions, instructions, and boundaries for their twin
- Active briefings injected into every twin prompt as high-priority context
- Briefing types: fact, opinion, instruction, availability, boundary
- Configurable expiry by date or usage count
- Maximum 10 active briefings per user
- Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-2--twin-briefing--context-injection)

#### 5.10 VIP Override / Relationship Tiers *(Phase 1 — alongside MVP)*
- Four sender tiers: VIP (bypass twin), Priority (always review), Standard, Cold
- User assigns tiers manually; twin suggests tier upgrades
- Tier 0 VIP messages never touch the twin — direct push to user
- Autonomous sending blocked for all Tier 0 and Tier 1 senders regardless of trust stage
- Spec: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-4--vip-override--relationship-tiers)

---

### Post-MVP Features

#### Phase 2
- GitHub integration (issues, PR reviews, comments)
- Slack / Discord integration
- YouTube comment management
- TikTok comment replies
- Calendar and scheduling (meeting prep briefs)
- Crisis / Surge Mode — auto-pause and crisis response templates on viral events
- Proactive Twin — outbound intelligence, deal signal detection, cold relationship nudges
- Multi-Identity Profiles — separate style models per audience (Creator, Professional, Business)
- Style Evolution / Identity Refresh — quarterly style checkpoints, intentional twin updates
- Twin Verification Public API — cryptographic verification for third-party integrators

#### Phase 3
- Real-time video call twin (you join as your avatar)
- Multi-language twin (speaks in your voice in other languages)
- Twin analytics dashboard (who it talked to, what it handled)
- Team twins (company-level digital representatives)
- API access for developers to build on top of SELPH
- On-Device Processing Mode — privacy-first mode for enterprise users
- Twin-to-Twin Protocol — structured negotiation between two SELPH twins

See full specs: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md)

---

## 6. User Flow

### Onboarding Flow
```
Sign Up
  ↓
Identity Verification (Gov ID + Face Match)
  ↓
Voice Recording (2–5 min speech)
  ↓
Avatar Recording (60-sec video)
  ↓
Connect Accounts (Instagram, Email, etc.)
  ↓
Personality Questionnaire (5 min)
  ↓
Twin Generated (processing: ~10 min)
  ↓
Review Your Twin (approve or refine)
  ↓
Set Operating Mode (Transparent / Private)
  ↓
Set Boundaries (what twin can / cannot handle)
  ↓
Twin Goes Live
```

### Daily Operation Flow
```
Message arrives on connected channel
  ↓
SELPH Twin analyzes context
  ↓
Twin drafts response in user's voice
  ↓
Confidence score assigned
  ↓
High confidence → sent to user for quick approval
Low confidence  → flagged, sent to user for full review
  ↓
User receives push notification
  ↓
User: Approve / Edit / Reject
  ↓
Response sent (with watermark if Transparent Mode)
  ↓
Twin logs action + learns from decision
```

---

## 7. Technical Requirements

### Performance
- Twin draft generation: <10 seconds
- Push notification delivery: <5 seconds after message received
- Avatar video response generation: <30 seconds
- Voice response generation: <5 seconds
- App load time: <2 seconds

### Scale
- Beta (Week 16): 500 concurrent twins, 50K messages/day
- Public launch (Month 6): 10,000 concurrent twins, 1M messages/day
- Growth target (Month 12): 100,000 concurrent twins, 10M messages/day
- 99.9% uptime SLA

### Security
- End-to-end encryption for all personal data
- On-device processing for sensitive identity data where possible
- SOC 2 Type II: audit initiated Month 3, certification by Month 9
- GDPR and CCPA compliant from day 1
- Deletion target within 24 hours, with legal maximum processing window of 30 days where required

### AI Stack
| Component | Technology |
|---|---|
| Core LLM | LiteLLM Gateway — 140+ models; user-selectable; BYOK; default: claude-sonnet-4-6 |
| Supported Models | Claude (Anthropic), GPT-5 (OpenAI), Gemini (Google), DeepSeek, Llama via Ollama, Mistral |
| Voice Clone | Chatterbox (MIT, free, default) — ElevenLabs (paid, optional) |
| Avatar Clone | Linly-Talker / Duix-Avatar (MIT, free, default) — HeyGen (paid, optional) |
| Local Model Option | Ollama — run open models on-device at zero cost |
| Memory | pgvector on Railway PostgreSQL (vector + structured, co-located) |
| Orchestration | LangGraph |
| Style Analysis | Fine-tuned NLP on user's content |
| Content Moderation | Custom classifier + third-party API |
| Watermarking | C2PA standard |

---

## 8. Business Model

| Tier | Price | Features |
|---|---|---|
| **Free** | $0/month | Basic twin, 50 interactions/month, no avatar |
| **Creator** | $39/month | Voice + avatar, 500 interactions, social integrations |
| **Pro** | $99/month | Unlimited interactions, all integrations, private mode |
| **Executive** | $299/month | Priority processing, advanced analytics, enterprise security |
| **Enterprise** | Custom | Per-seat, SSO, admin controls, compliance, SLA |

---

## 9. Go-To-Market Plan

### Phase 1 — Creator Launch (Month 1–2)
- Private beta with 50 selected content creators
- Gather feedback, improve twin accuracy
- Build case studies and testimonials

### Phase 2 — Public Launch (Month 3)
- Open waitlist → rolling invites
- Creator referral program: "Invite a creator, get 1 month free"
- PR push: "The first AI that IS you, not just helps you"

### Phase 3 — Segment Expansion (Month 4–6)
- Launch Pro tier for consultants and developers
- GitHub, Slack, Discord integrations
- Developer community outreach

### Phase 4 — Enterprise (Month 7–12)
- Enterprise tier with admin controls
- Security certifications (SOC 2)
- Direct sales to companies

---

## 10. Risks & Mitigations

See:
- [RISK_MITIGATION.md](../04-safety/RISK_MITIGATION.md)
- [SELPH_Canonical-Policy-Matrix.md](../04-safety/SELPH_Canonical-Policy-Matrix.md)

---

## 11. Out of Scope (v1.0)

- Real-time video call avatar (Phase 3)
- Multi-language twin (Phase 3)
- Twin-to-twin communication
- Financial transaction handling
- Legal document signing
- Medical or clinical advice

---

## 12. Open Questions

- [ ] Which open-source avatar tool gives best quality for MVP: Linly-Talker vs Duix-Avatar? When should HeyGen (paid) be offered as optional premium?
- [ ] How do we handle twin identity when user's style changes significantly over time?
- [ ] What's the minimum voice recording length needed for a high-quality clone?
- [ ] Should free tier have avatar at all, or voice-only?
- [ ] How do we handle multi-platform identity consistency (user sounds different on LinkedIn vs Instagram)?
- [ ] Instagram Business Account requirement — how do we guide personal-account creators through the upgrade process? Do we support personal accounts via unofficial methods or require business upgrade?
- [ ] WhatsApp Business API approval from Meta can take weeks — what's our fallback for early users who want WhatsApp support?

---

## Appendix: File Structure

```
SELPH/docs/
├── 01-product/    PRODUCT_IDEA.md, PRD.md
├── 02-market/     VALIDATION.md, FEATURE_VALIDATION_AND_EXPANSION.md
├── 03-specs/      SELPH_Twin-Engine-Spec.md, SELPH_Identity-Model-Spec.md, SELPH_Feature-Expansion-Spec.md
├── 04-safety/     RISK_MITIGATION.md, SELPH_Privacy-Consent.md, SELPH_Canonical-Policy-Matrix.md
├── 05-technical/  SELPH_System-Architecture.md, SELPH_Database-Schema.md, SELPH_API-Design.md
└── 06-implementation/ MVP_BUILD_PLAN.md, BUILD_READINESS_ACTION_PLAN.md, BUILD_READINESS_SCORECARD.md,
                       SPRINT_PLAN_2_WEEKS.md, REFERENCES.md, INVESTOR_ONE_PAGER.md
```

---

*Status: PRD v1.0 — Ready for Architecture Phase*
