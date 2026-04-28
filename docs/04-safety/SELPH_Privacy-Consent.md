# SELPH — Privacy & Consent Architecture

> Version: 1.0
> Created: 2026-04-24
> Folder: 04-safety
> Status: Draft — Legal requirement, must be built before any user data is collected

---

## Overview

SELPH collects some of the most sensitive personal data possible — voice recordings, facial video, device data, private messages, and communication history. This document specifies the consent architecture, data classification, retention policies, and compliance framework that governs how this data is handled.

This is not optional. Every component in this document must be built before the first real user signs up.

Policy precedence and final enforceable values are defined in:
- [SELPH_Canonical-Policy-Matrix.md](./SELPH_Canonical-Policy-Matrix.md)

---

## Data Classification

| Data Type | Sensitivity | Examples | Storage |
|---|---|---|---|
| **Biometric** | Critical | Voice recordings, facial video for avatar | Encrypted Cloudflare R2, on-device processing first |
| **Identity** | Critical | Government ID, face match result | Encrypted DB, retention limited to verification only |
| **Communication** | High | Ingested emails, DMs, social posts | Encrypted DB + pgvector (on Railway PostgreSQL) |
| **Behavioral** | High | Approval/rejection patterns, interaction history | PostgreSQL, encrypted |
| **Profile** | Medium | Tone, vocabulary, personality settings | PostgreSQL |
| **Usage** | Low | App interactions, feature usage | Analytics DB |

---

## Consent Architecture

### Principle: Granular, Explicit, Revocable

SELPH uses **layered consent** — users consent to each data category separately. No bundled consent.

```
Layer 1 — Account Consent (required)
├── Terms of Service
├── Privacy Policy
└── Digital Twin Agreement (specific to AI representation)

Layer 2 — Identity Consent (required for twin creation)
├── Identity verification (Gov ID + face match)
├── Voice recording and clone creation
└── Avatar recording and clone creation

Layer 3 — Data Ingestion Consent (required per channel)
├── Instagram content ingestion
├── Email content ingestion
└── Twitter/X content ingestion

Layer 4 — Operating Mode Consent (required per mode)
├── Transparent Mode: recipient disclosure agreement
└── Private Mode: user acknowledges AI-drafted content responsibility

Layer 5 — Optional Features (opt-in)
├── Device data access
└── Contact list access (for sender context)
```

---

## Consent Capture Flow

### Onboarding Consent Screens

```
Screen 1 — Welcome & What SELPH Does
  "SELPH creates a digital twin of you. Here's exactly what that means..."
  [Plain language explanation — no legal jargon]
  [✓ I understand and want to continue]

Screen 2 — Digital Twin Agreement
  "By creating a twin, you authorize SELPH to:
   ✓ Record and clone your voice
   ✓ Record and create your avatar
   ✓ Analyze your writing style from connected accounts
   ✓ Draft responses on your behalf (always with your approval)"
  [Read full agreement] [✓ I agree — signed as [Name] on [Date]]

Screen 3 — Identity Verification
  "We verify your identity to ensure only YOU can create your twin."
  [Why we need this: prevent impersonation, protect you legally]
  [✓ Verify my identity]

Screen 4 — Voice Recording Consent
  "Your voice recording will be:
   ✓ Encrypted and stored securely
   ✓ Used only to generate responses on your behalf
   ✗ Never sold or shared with third parties
   ✗ Never used to train AI models without your explicit consent"
  [✓ I consent to voice cloning]

Screen 5 — Avatar Recording Consent
  "Your video will be:
   ✓ Processed to create your avatar model
   ✓ Used only for video responses you approve
   ✗ Never stored as raw video after processing (unless you choose)
   ✗ Never used without your explicit approval per response"
  [✓ I consent to avatar creation]

Screen 6 — Data Ingestion (per channel)
  "Connect Instagram to teach your twin your writing style.
   We will read: your last 500 captions and DM replies
   We will NOT: post, follow, or modify anything"
  [✓ Connect Instagram] [Skip for now]
```

---

## Consent Storage

```sql
user_consents (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  consent_type    VARCHAR(100) NOT NULL,
  -- consent_type values:
  --   "terms_of_service", "privacy_policy", "digital_twin_agreement",
  --   "identity_verification", "voice_clone", "avatar_clone",
  --   "instagram_ingestion", "gmail_ingestion", "twitter_ingestion",
  --   "transparent_mode", "private_mode"
  version         VARCHAR(20) NOT NULL,   -- document version e.g. "1.0", "1.1"
  granted         BOOLEAN NOT NULL,
  granted_at      TIMESTAMPTZ,
  revoked_at      TIMESTAMPTZ,
  ip_address      INET NOT NULL,
  user_agent      TEXT NOT NULL,
  geo_country     VARCHAR(2),             -- ISO country code for jurisdiction
  signature_text  TEXT,                  -- what the user acknowledged
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
)

CREATE INDEX idx_consents_user ON user_consents(user_id, consent_type);
CREATE INDEX idx_consents_granted ON user_consents(user_id, granted, consent_type);
```

---

## Data Retention Policies

| Data Type | Retention Period | Deletion Trigger |
|---|---|---|
| Government ID | Deleted immediately after verification | Verification complete |
| Face match result | 30 days | Auto-delete |
| Raw voice recordings | 90 days after clone creation | User request or auto |
| Voice model (Chatterbox/provider) | Until account deleted | Account deletion or user request |
| Raw avatar video | 90 days after model creation | User request or auto |
| Avatar model (Linly-Talker/provider) | Until account deleted | Account deletion or user request |
| Ingested social content | Until account deleted or consent revoked | Consent revocation or account deletion |
| Identity profile | Until account deleted | Account deletion |
| Approved drafts / samples | Until account deleted | Account deletion |
| Audit logs | 2 years | Legal hold or account deletion |
| Usage analytics | 1 year (anonymized after 90 days) | Auto-anonymize |

---

## Data Subject Rights (GDPR / CCPA)

### Right to Access
```
User requests: "What data does SELPH have about me?"
Response within: 30 days (GDPR), 45 days (CCPA)
Delivery: Downloadable ZIP containing:
  ├── identity_profiles.json        — all profiles (multi-identity)
  ├── vocabulary.json
  ├── topics.json
  ├── sample_responses.json
  ├── twin_briefings.json           — all briefings (active and cleared)
  ├── sender_tiers.json             — VIP and tier assignments
  ├── audit_logs.json
  ├── consent_history.json
  ├── draft_history.json (last 90 days)
  ├── proactive_suggestions.json    — suggestion history
  └── style_checkpoints.json        — style evolution history
```

### Right to Erasure ("Delete My Twin")
```
User requests account + twin deletion
Timeline: Target completion within 24 hours, with legal maximum processing window of 30 days where required
Process:
  1. Pause twin immediately (no new actions)
  2. Delete voice model via provider API (Chatterbox default, or ElevenLabs if premium opted in)
  3. Delete avatar model via provider API (Linly-Talker default, or HeyGen if premium opted in)
  4. Delete all PostgreSQL records (cascade)
  5. Delete all pgvector embeddings by user_id (CASCADE via PostgreSQL ON DELETE CASCADE)
  6. Delete all Cloudflare R2 files in user folder
  7. Send confirmation email with deletion certificate
  8. Retain only: anonymized audit logs (legal requirement, 2 years)
```

### Right to Portability
```
User exports their twin data to use elsewhere
Delivered as: JSON + MP3 (voice samples) + MP4 (avatar sample)
All data in open formats — no vendor lock-in
```

### Right to Restrict Processing
```
User can pause specific data uses without full deletion:
  ├── Pause voice clone (keep profile, disable voice responses)
  ├── Pause avatar (keep profile, disable video responses)
  ├── Pause learning (stop updating profile from new feedback)
  └── Pause twin entirely (keep data, stop all activity)
```

---

## EU AI Act Compliance (August 2026)

SELPH falls under the EU AI Act as a **"Limited Risk AI System"** (AI interacting with humans).

### Mandatory Requirements

```
1. Transparency Obligation
   ✓ Transparent Mode is default — all recipients told they're talking to an AI twin
   ✓ Every twin-generated output carries "SELPH Digital Twin" label in Transparent Mode
   ✓ Verification URL: selph.ai/verify/{twin_id}

2. AI Labeling on Generated Content
   ✓ All text: invisible C2PA watermark + visible label option
   ✓ All audio: AI speech detection metadata (Chatterbox watermark or provider equivalent)
   ✓ All video: AI video watermark + SELPH overlay (Linly-Talker default or provider equivalent)

3. Human Oversight
  ✓ Stage 1 and Stage 2 use human approval by default for outbound actions
  ✓ Limited low-risk autonomy in Stage 2 requires explicit user opt-in
  ✓ High-risk categories remain blocked from autonomous execution

4. No Prohibited Uses
   ✗ Social scoring: SELPH does not score individuals
   ✗ Subliminal manipulation: SELPH only sends messages user approves
   ✗ Biometric categorization: Identity verification only, no classification
```

---

## Voice & Avatar — Special Protections

Voice and facial data are **biometric data** under GDPR Article 9 (special category). Requires explicit, specific consent.

```
Voice Data Protections:
├── Processed in encrypted pipeline only
├── Raw audio deleted after clone creation (within 90 days)
├── Voice model stored under user_id — never linked to name in voice provider (Chatterbox/ElevenLabs)
├── Voice model ID is encrypted in our DB
├── User can delete voice model at any time from settings
└── Never used to train any AI model without separate explicit consent

Avatar Data Protections:
├── Video processed to extract facial geometry only
├── Raw video deleted after model creation (within 90 days, user option to keep)
├── Avatar model stored under anonymous ID in avatar provider (Linly-Talker/HeyGen)
├── Every avatar video generated is user-approved before sending
└── Transparent Mode watermark applied to all avatar videos
```

---

## India IT Rules 2026 Compliance

```
Requirement: 3-hour takedown for harmful AI-generated content
SELPH Implementation:
├── Dedicated abuse report endpoint: POST /report/twin/{twin_id}
├── Auto-suspend account within 15 minutes of high-severity report
├── Human review team notified immediately
├── Content removed from all channels within 3 hours
└── Reporting user notified of action taken

Labeling Requirement: AI-generated content must be identifiable
SELPH Implementation:
├── C2PA metadata on all generated content
├── "AI Generated by SELPH" label in Transparent Mode
└── All content traceable to SELPH account via watermark
```

---

## On-Device Processing Strategy

Where possible, sensitive data is processed on-device before being sent to SELPH servers. In Phase 3, an explicit **On-Device Processing Mode** is available for privacy-conscious users (see [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md#feature-9--privacy--on-device-processing-mode)).

```
On-Device (never sent to server in raw form):
├── Government ID — processed by on-device OCR + face match SDK
├── Initial voice analysis — feature extraction on device, not raw audio
└── Private message content — hashed before sending for content matching

Sent to Server (encrypted in transit):
├── Processed voice features for clone creation (not raw audio)
├── Writing style analysis results (not raw messages)
└── Identity profile (stored encrypted at rest)

Sent to Third-Party APIs (anonymized):
├── Voice provider (Chatterbox self-hosted default, or ElevenLabs if opted in): voice samples (no name, just user_id)
├── Avatar provider (Linly-Talker self-hosted default, or HeyGen if opted in): avatar video (no name, just user_id)
└── LLM provider (user-selected via LiteLLM — Claude, GPT, Gemini, Ollama, etc.): incoming message + draft (no PII beyond what user approves)
```

### On-Device Processing Mode (Phase 3 — Opt-In)

When enabled, style analysis and text draft generation run on-device via Apple Intelligence or Google Gemini Nano. Only anonymized embeddings sync to the cloud. Voice clone and avatar always require cloud processing. All on-device drafts route to mandatory human review (no confidence scoring in on-device mode). See privacy settings: `processing_mode = on_device | hybrid | cloud`.

---

## Privacy-by-Design Checklist

Before shipping any phase, verify:

```
Phase 0 — Foundation:
- [ ] Consent tables created in DB
- [ ] Consent capture screens built
- [ ] Privacy policy v1.0 published
- [ ] Data deletion endpoint functional

Phase 1 — Identity Core:
- [ ] Voice consent screen implemented
- [ ] Avatar consent screen implemented
- [ ] On-device ID verification integrated
- [ ] Raw data auto-delete scheduled

Phase 4 — Safety Layer:
- [ ] C2PA watermarking on all text outputs
- [ ] Audit log capturing all actions
- [ ] Abuse report endpoint live
- [ ] 3-hour takedown SLA workflow active

Phase 5 — Channel Integration:
- [ ] Per-channel consent captured before ingestion
- [ ] Channel data deletion works on consent revocation
- [ ] EU AI Act labeling active in Transparent Mode
```

---

*Status: Privacy & Consent Architecture v1.0 — Must be implemented before first user onboards*
