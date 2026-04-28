# SELPH — API Design

> Version: 1.0
> Created: 2026-04-24
> Folder: 05-technical
> Status: Draft — Request/response contracts for all endpoints

---

## Overview

This document defines every API endpoint in SELPH — the URL, method, request body, response shape, auth requirements, and error codes. This is the contract between the FastAPI backend and the React Native mobile app.

Base URL: `https://api.selph.ai/v1`

---

## Auth

All endpoints except `/auth/*` and `/webhooks/*` require:

```
Authorization: Bearer <access_token>
```

Access tokens are RS256 JWTs with 15-minute TTL. Refresh tokens live 7 days.

---

## Auth Endpoints

### `POST /auth/register`

```json
// Request
{
  "email": "alex@example.com",
  "password": "...",
  "full_name": "Alex Rivera"
}

// Response 201
{
  "user_id": "uuid",
  "email": "alex@example.com",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900
}

// Errors
400 — invalid input
409 — email already registered
```

---

### `POST /auth/login`

```json
// Request
{
  "email": "alex@example.com",
  "password": "..."
}

// Response 200
{
  "user_id": "uuid",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900
}

// Errors
401 — invalid credentials
403 — account suspended
```

---

### `POST /auth/refresh`

```json
// Request
{
  "refresh_token": "eyJ..."
}

// Response 200
{
  "access_token": "eyJ...",
  "expires_in": 900
}

// Errors
401 — invalid or expired refresh token
```

---

### `POST /auth/logout`

```json
// Request
{
  "refresh_token": "eyJ..."
}

// Response 204 — no body
```

---

## Consent Endpoints

### `POST /consent`

Grant or revoke a consent item.

```json
// Request
{
  "consent_type": "voice_clone",
  "version": "1.0",
  "granted": true,
  "signature_text": "I consent to voice cloning as described"
}

// Response 201
{
  "consent_id": "uuid",
  "consent_type": "voice_clone",
  "granted": true,
  "granted_at": "2026-04-24T10:00:00Z"
}

// Errors
400 — invalid consent_type
409 — consent already exists in this state
```

---

### `GET /consent`

Return all consent records for the authenticated user.

```json
// Response 200
{
  "consents": [
    {
      "consent_type": "terms_of_service",
      "version": "1.0",
      "granted": true,
      "granted_at": "2026-04-24T09:00:00Z",
      "revoked_at": null
    },
    {
      "consent_type": "voice_clone",
      "version": "1.0",
      "granted": true,
      "granted_at": "2026-04-24T09:05:00Z",
      "revoked_at": null
    }
  ]
}
```

---

## Identity / Twin Profile Endpoints

### `POST /identity/profile`

Create the initial twin profile (called once during onboarding).

```json
// Request
{
  "first_name": "Alex",
  "last_name": "Rivera",
  "domain": "content creator",
  "sub_domain": "fitness",
  "professional_title": "YouTuber",
  "tone": "casual, warm, motivational",
  "formality_level": 2,
  "avg_response_length": 80,
  "response_length_min": 20,
  "response_length_max": 200,
  "emoji_usage": 0.4,
  "greeting_style": "Hey!",
  "sign_off_style": "Keep going 💪",
  "personality_words": ["warm", "motivational", "direct"],
  "bio_summary": "Fitness creator helping people build sustainable habits"
}

// Response 201
{
  "profile_id": "uuid",
  "version": 1,
  "created_at": "2026-04-24T09:10:00Z"
}

// Errors
409 — profile already exists for this user
```

---

### `GET /identity/profile`

```json
// Response 200
{
  "profile_id": "uuid",
  "version": 5,
  "first_name": "Alex",
  "last_name": "Rivera",
  "domain": "content creator",
  "sub_domain": "fitness",
  "tone": "casual, warm, motivational",
  "formality_level": 2,
  "personality_words": ["warm", "motivational", "direct"],
  "trust_stage": 1,
  "approval_rate": 0.71,
  "total_drafts": 24,
  "total_approved": 17,
  "total_edited": 5,
  "total_rejected": 2,
  "identity_confidence": 0.48,
  "updated_at": "2026-04-24T10:30:00Z"
}
```

---

### `PATCH /identity/profile`

Update specific profile fields.

```json
// Request — only include fields to change
{
  "tone": "casual, warm, energetic",
  "greeting_style": "Heyyy!"
}

// Response 200
{
  "profile_id": "uuid",
  "version": 6,
  "updated_at": "2026-04-24T11:00:00Z"
}
```

---

### `GET /identity/topics`

```json
// Response 200
{
  "topics": [
    { "topic": "fitness", "type": "expert", "confidence": 0.95 },
    { "topic": "nutrition", "type": "known", "confidence": 0.80 },
    { "topic": "politics", "type": "avoided", "confidence": 1.0 }
  ]
}
```

---

### `POST /identity/topics`

```json
// Request
{
  "topic": "mental health",
  "type": "known",
  "source": "user_stated"
}

// Response 201
{
  "topic_id": "uuid",
  "topic": "mental health",
  "type": "known"
}
```

---

### `DELETE /identity/topics/{topic_id}`

```
// Response 204 — no body
```

---

### `GET /identity/confidence`

Returns the identity confidence score displayed in the app.

```json
// Response 200
{
  "score": 0.48,
  "label": "Your twin knows you at 48%",
  "factors": {
    "sample_count": 0.48,
    "approval_rate": 0.71,
    "topic_coverage": 0.30,
    "vocab_coverage": 0.60,
    "days_active": 0.03
  },
  "next_milestone": {
    "score": 0.70,
    "label": "Approve 10 more drafts to reach 70%"
  }
}
```

---

## Channel Endpoints

### `GET /channels/instagram/auth`

Returns the OAuth URL for Instagram authorization.

```json
// Response 200
{
  "auth_url": "https://api.instagram.com/oauth/authorize?...",
  "state": "csrf_state_token"
}
```

---

### `POST /channels/instagram/callback`

Exchange OAuth code for access token.

```json
// Request
{
  "code": "oauth_code",
  "state": "csrf_state_token"
}

// Response 200
{
  "channel": "instagram_dm",
  "platform_user_id": "instagram_user_id",
  "connected_at": "2026-04-24T09:15:00Z",
  "ingestion_status": "pending"
}

// Errors
400 — invalid code or state mismatch
403 — consent not granted for instagram_ingestion
```

---

### `GET /channels/gmail/auth`

Returns the OAuth URL for Gmail authorization.

```json
// Response 200
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "csrf_state_token"
}
```

---

### `POST /channels/gmail/callback`

```json
// Request
{
  "code": "oauth_code",
  "state": "csrf_state_token"
}

// Response 200
{
  "channel": "gmail",
  "platform_user_id": "alex@gmail.com",
  "connected_at": "2026-04-24T09:16:00Z",
  "ingestion_status": "pending"
}
```

---

### `GET /channels`

List all connected channels and their status.

```json
// Response 200
{
  "channels": [
    {
      "channel": "instagram_dm",
      "connected": true,
      "platform_user_id": "instagram_user_id",
      "ingestion_status": "complete",
      "last_sync_at": "2026-04-24T09:30:00Z"
    },
    {
      "channel": "gmail",
      "connected": true,
      "platform_user_id": "alex@gmail.com",
      "ingestion_status": "in_progress",
      "last_sync_at": null
    }
  ]
}
```

---

### `DELETE /channels/{channel}`

Disconnect a channel. Triggers consent revocation and data deletion.

```
// Response 204 — no body
// Side effects: channel data deleted per consent revocation policy
```

---

## Draft Endpoints

### `GET /drafts/pending`

List all drafts waiting for human action.

```json
// Response 200
{
  "drafts": [
    {
      "draft_id": "uuid",
      "channel": "instagram_dm",
      "sender_name": "Jordan",
      "incoming_message": "Hey! Do you have a beginner program?",
      "draft_preview": "Hey Jordan! Yeah absolutely — I've got...",
      "confidence_score": 0.88,
      "confidence_label": "ready",
      "created_at": "2026-04-24T10:45:00Z",
      "expires_at": "2026-04-25T10:45:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /drafts/{draft_id}`

Full draft detail for the review screen.

```json
// Response 200
{
  "draft_id": "uuid",
  "channel": "instagram_dm",
  "sender_id": "instagram_sender_id",
  "sender_name": "Jordan",
  "sender_interaction_count": 3,
  "incoming_message": "Hey! Do you have a beginner program?",
  "draft_content": "Hey Jordan! Yeah absolutely — I've got a free 4-week starter guide. Want me to DM you the link? 🙌",
  "confidence_score": 0.88,
  "confidence_label": "ready",
  "confidence_factors": {
    "topic_known": 0.95,
    "length_match": 0.90,
    "tone_match": 0.87,
    "no_avoided_topics": 1.0,
    "sample_similarity": 0.76
  },
  "reasoning": "User is asking about beginner programs — directly in the fitness domain with high confidence.",
  "moderation_passed": true,
  "moderation_flags": [],
  "status": "pending",
  "created_at": "2026-04-24T10:45:00Z",
  "expires_at": "2026-04-25T10:45:00Z"
}

// Errors
404 — draft not found
403 — draft belongs to different user
```

---

### `POST /drafts/{draft_id}/approve`

Approve the draft as-is. Sends the message.

```json
// Request — no body required

// Response 200
{
  "draft_id": "uuid",
  "action": "approved",
  "message_sent": true,
  "actioned_at": "2026-04-24T10:47:00Z"
}

// Errors
409 — draft already actioned
410 — draft expired
```

---

### `POST /drafts/{draft_id}/edit`

Approve an edited version. Sends the edited content.

```json
// Request
{
  "edited_content": "Hey Jordan! Yes I do — check out my free 4-week beginner guide in my bio 🙌 DM me if you want tips to get started!"
}

// Response 200
{
  "draft_id": "uuid",
  "action": "edited",
  "message_sent": true,
  "actioned_at": "2026-04-24T10:48:00Z"
}

// Errors
400 — edited_content empty or exceeds 5000 chars
409 — draft already actioned
```

---

### `POST /drafts/{draft_id}/reject`

Reject the draft. No message is sent. Records rejection reason for learning.

```json
// Request
{
  "reason": "wrong_tone"
  // reason values: "wrong_tone" | "wrong_facts" | "too_long" | "too_short"
  //                "off_topic" | "privacy_concern" | "other"
}

// Response 200
{
  "draft_id": "uuid",
  "action": "rejected",
  "actioned_at": "2026-04-24T10:49:00Z"
}
```

---

### `POST /drafts/{draft_id}/skip`

Skip without acting. No message sent. No learning signal.

```json
// Request — no body

// Response 200
{
  "draft_id": "uuid",
  "action": "skipped",
  "actioned_at": "2026-04-24T10:50:00Z"
}
```

---

## Voice & Avatar Endpoints

### `POST /biometric/voice/upload`

Upload voice recording for clone creation.

```
Content-Type: multipart/form-data

// Form fields
file: <audio file — MP3 or WAV, max 50MB>
consent_confirmed: true   // must match consent record

// Response 202
{
  "upload_id": "uuid",
  "s3_key": "users/{user_id}/voice/recording.mp3",
  "status": "recording_uploaded",
  "clone_job_id": "celery_task_id"
}

// Errors
400 — file missing, wrong format, or consent_confirmed=false
403 — voice_clone consent not granted
```

---

### `POST /biometric/avatar/upload`

Upload avatar video for clone creation.

```
Content-Type: multipart/form-data

// Form fields
file: <video file — MP4, max 200MB>
consent_confirmed: true

// Response 202
{
  "upload_id": "uuid",
  "s3_key": "users/{user_id}/avatar/recording.mp4",
  "status": "video_uploaded",
  "clone_job_id": "celery_task_id"
}

// Errors
400 — file missing, wrong format, or consent_confirmed=false
403 — avatar_clone consent not granted
```

---

### `GET /biometric/status`

Check voice and avatar creation status.

```json
// Response 200
{
  "voice": {
    "status": "clone_ready",
    "created_at": "2026-04-24T09:45:00Z",
    "raw_delete_scheduled_at": "2026-07-23T09:45:00Z"
  },
  "avatar": {
    "status": "avatar_creating",
    "created_at": null,
    "raw_delete_scheduled_at": null
  }
}
```

---

### `DELETE /biometric/voice`

Delete voice clone model.

```json
// Response 200
{
  "deleted": true,
  "deleted_at": "2026-04-24T11:00:00Z",
  "elevenlabs_confirmed": true
}
```

---

### `DELETE /biometric/avatar`

Delete avatar model.

```json
// Response 200
{
  "deleted": true,
  "deleted_at": "2026-04-24T11:00:00Z",
  "heygen_confirmed": true
}
```

---

## Account / Privacy Endpoints

### `GET /account/export`

Request a data export ZIP. Queues the job and returns an export ID to poll.

```json
// Response 202 — job queued
{
  "export_id": "uuid",
  "status": "preparing",
  "estimated_ready_in_seconds": 120
}
```

---

### `GET /account/export/{export_id}`

Poll for export status. When ready, returns a pre-signed Cloudflare R2 download URL (1-hour TTL).

```json
// Response 200 — still preparing
{
  "export_id": "uuid",
  "status": "preparing"
}

// Response 200 — ready
{
  "export_id": "uuid",
  "status": "ready",
  "download_url": "https://selph-exports.s3.amazonaws.com/...",
  "expires_at": "2026-04-25T11:00:00Z"
}

// Errors
404 — export_id not found or belongs to different user
```

---

### `DELETE /account`

Delete account and all associated data. Irreversible.

```json
// Request — email auth users
{
  "confirmation": "DELETE MY ACCOUNT",   // must be exactly this string
  "password": "..."                      // required for email auth users
}

// Request — social auth users (Google/Apple — no password)
{
  "confirmation": "DELETE MY ACCOUNT",
  "auth_provider_token": "..."           // fresh provider token to re-verify identity
}

// Response 200
{
  "deletion_scheduled": true,
  "estimated_completion": "2026-04-25T11:00:00Z",
  "certificate_email": "alex@example.com"
}

// Errors
400 — confirmation string wrong
401 — password incorrect or provider token invalid
```

---

## Webhook Endpoints (Platform → SELPH)

These endpoints receive incoming messages from connected platforms. They are not authenticated with JWT — they use HMAC-SHA256 signature verification.

### `POST /webhooks/instagram`

```
Headers:
  X-Hub-Signature-256: sha256=<hmac>

Body: Meta Graph API webhook payload (varies by event type)

Response: 200 (must respond within 5 seconds — processing is async)
```

---

### `POST /webhooks/gmail`

```
Headers:
  Authorization: Bearer <google_pubsub_token>

Body: Google Pub/Sub push message (base64-encoded Gmail notification)

Response: 200
```

---

### `POST /webhooks/twitter`

```
Headers:
  X-Twitter-Webhooks-Signature: sha256=<hmac>

Body: Twitter Account Activity API event payload

Response: 200
```

---

## Twin Briefing Endpoints

### `GET /briefings`

List all briefings for the authenticated user.

```json
// Response 200
{
  "briefings": [
    {
      "briefing_id": "uuid",
      "briefing_type": "fact",
      "topic": "new course launch",
      "content": "My new 8-week program launches Friday at mysite.com/program",
      "priority": 8,
      "is_active": true,
      "expires_at": "2026-05-03T00:00:00Z",
      "use_count": 12,
      "created_at": "2026-04-27T09:00:00Z"
    }
  ],
  "total": 1,
  "active_count": 1,
  "max_active": 10
}
```

---

### `POST /briefings`

Create a new briefing.

```json
// Request
{
  "briefing_type": "fact",
  "topic": "new course launch",
  "content": "My new 8-week program launches Friday at mysite.com/program",
  "priority": 8,
  "expires_at": "2026-05-03T00:00:00Z",
  "max_uses": null
}

// Response 201
{
  "briefing_id": "uuid",
  "is_active": true,
  "created_at": "2026-04-27T09:00:00Z"
}

// Errors
400 — invalid briefing_type or missing content
409 — active briefing limit (10) reached
```

---

### `DELETE /briefings/{briefing_id}`

Clear a briefing immediately.

```
// Response 204 — no body
// Side effect: briefing is_active set to false, cleared_at recorded
```

---

## Sender Tier Endpoints

### `GET /senders/tiers`

List all sender tier assignments.

```json
// Response 200
{
  "tiers": [
    {
      "sender_id": "instagram_sender_123",
      "platform": "instagram_dm",
      "tier": 0,
      "tier_label": "VIP",
      "set_by": "user",
      "notes": "Top sponsor contact"
    }
  ]
}
```

---

### `POST /senders/tiers`

Assign a tier to a sender.

```json
// Request
{
  "sender_id": "instagram_sender_123",
  "platform": "instagram_dm",
  "tier": 0,
  "notes": "Top sponsor contact"
}

// Response 201
{
  "tier_id": "uuid",
  "sender_id": "instagram_sender_123",
  "tier": 0
}

// Errors
400 — invalid tier (must be 0–3) or missing sender_id
```

---

### `PATCH /senders/tiers/{tier_id}`

Update a sender's tier.

```json
// Request
{ "tier": 1, "notes": "Moved to priority" }

// Response 200
{ "tier_id": "uuid", "tier": 1, "updated_at": "..." }
```

---

## Batch Approval Endpoints

### `GET /batches/pending`

List pending message clusters awaiting template approval.

```json
// Response 200
{
  "batches": [
    {
      "cluster_id": "uuid",
      "cluster_label": "workout routine question",
      "cluster_summary": "142 messages asking about your workout routine",
      "message_count": 142,
      "template_draft": "Hey {sender_name}! Great question about my routine...",
      "status": "pending",
      "created_at": "2026-04-27T10:00:00Z"
    }
  ],
  "total": 3
}
```

---

### `POST /batches/{cluster_id}/approve`

Approve a batch template (optionally with edits).

```json
// Request
{
  "approved_template": "Hey {sender_name}! Great question — I do...",
  "exclude_sender_ids": ["sender_abc"]
}

// Response 200
{
  "cluster_id": "uuid",
  "approved_at": "...",
  "messages_queued": 141
}
```

---

### `POST /batches/{cluster_id}/reject`

Reject a batch cluster — messages go to individual queue.

```json
// Response 200
{ "cluster_id": "uuid", "status": "rejected" }
```

---

## Proactive Suggestion Endpoints

### `GET /suggestions`

List pending proactive suggestions.

```json
// Response 200
{
  "suggestions": [
    {
      "suggestion_id": "uuid",
      "suggestion_type": "cold_relationship",
      "signal_summary": "No reply to Marcus in 16 days",
      "draft_message": "Hey Marcus! Just wanted to check in...",
      "urgency_score": 0.72,
      "value_score": 0.85,
      "status": "pending",
      "created_at": "..."
    }
  ]
}
```

---

### `POST /suggestions/{suggestion_id}/approve`

Send the proactive draft.

```json
// Response 200
{ "suggestion_id": "uuid", "action": "approved", "message_sent": true }
```

---

### `POST /suggestions/{suggestion_id}/dismiss`

Snooze or permanently dismiss the suggestion.

```json
// Request
{ "snooze_days": 30 }  // null = never show again

// Response 200
{ "suggestion_id": "uuid", "action": "dismissed", "snoozed_until": "..." }
```

---

## Crisis Mode Endpoints

### `GET /crisis/status`

Get current twin operating mode and any active surge event.

```json
// Response 200
{
  "mode": "normal",
  "surge_event": null
}

// Response 200 (during crisis)
{
  "mode": "crisis_mode",
  "surge_event": {
    "event_id": "uuid",
    "trigger_type": "volume_surge",
    "surge_ratio": 8.3,
    "activated_at": "2026-04-27T15:00:00Z"
  }
}
```

---

### `POST /crisis/activate`

Manually activate crisis mode.

```json
// Request — no body

// Response 200
{ "mode": "crisis_mode", "activated_at": "..." }
```

---

### `POST /crisis/resume`

Resume normal twin operation after crisis.

```json
// Response 200
{ "mode": "normal", "resolved_at": "..." }
```

---

## Multi-Identity Profile Endpoints

### `GET /identity/profiles`

List all identity profiles for the user.

```json
// Response 200
{
  "profiles": [
    {
      "profile_id": "uuid",
      "profile_name": "Creator",
      "profile_type": "personal_brand",
      "is_primary": true,
      "approval_rate": 0.84,
      "channels": ["instagram_dm", "tiktok"]
    },
    {
      "profile_id": "uuid",
      "profile_name": "Professional",
      "profile_type": "professional",
      "is_primary": false,
      "approval_rate": 0.79,
      "channels": ["gmail", "linkedin"]
    }
  ]
}
```

---

### `POST /identity/profiles`

Create a new identity profile.

```json
// Request — same fields as POST /identity/profile
{
  "profile_name": "Professional",
  "profile_type": "professional",
  "tone": "formal, direct, concise",
  ...
}

// Response 201
{ "profile_id": "uuid", "profile_name": "Professional" }
```

---

### `PATCH /identity/profiles/{profile_id}`

Update a specific profile.

```json
// Request — same as PATCH /identity/profile
{ "tone": "direct, warm" }

// Response 200
{ "profile_id": "uuid", "version": 3 }
```

---

### `POST /identity/profiles/{profile_id}/channels`

Assign a channel to a profile.

```json
// Request
{ "channel": "linkedin", "platform_account": "alex-rivera" }

// Response 201
{ "mapping_id": "uuid" }

// Errors
409 — channel already mapped to another profile
```

---

## Style Checkpoint Endpoints

### `GET /identity/checkpoints`

List style checkpoints (pending decisions and history).

```json
// Response 200
{
  "checkpoints": [
    {
      "checkpoint_id": "uuid",
      "trigger_type": "automatic",
      "divergence_score": 0.24,
      "decision": null,
      "created_at": "2026-04-27T00:00:00Z"
    }
  ]
}
```

---

### `POST /identity/checkpoints/{checkpoint_id}/decide`

Accept or decline a style update.

```json
// Request
{
  "decision": "update",  // "update" | "keep" | "partial"
  "updated_dimensions": ["tone", "emoji_usage"]  // only for "partial"
}

// Response 200
{ "checkpoint_id": "uuid", "decision": "update", "new_profile_version": 4 }
```

---

## Twin Verification Endpoint (Public — no auth required)

### `GET /verify/{twin_id}`

Verify that a twin-generated message is authentic. Public endpoint.

```json
// Response 200 — valid
{
  "valid": true,
  "twin_id": "twn_8f3k2m9p",
  "owner_name": "Alex Chen",
  "owner_verified": true,
  "generated_at": "2026-04-27T14:23:00Z",
  "mode": "transparent"
}

// Response 200 — invalid
{
  "valid": false,
  "reason": "signature_mismatch",
  "twin_id": "twn_8f3k2m9p"
}

// Response 404 — twin not found
{ "valid": false, "reason": "twin_not_found" }
```

---

## WebSocket Endpoint

### `WS /ws/drafts`

Persistent WebSocket connection for real-time draft events. Requires JWT auth as query param.

```
Connection: wss://api.selph.ai/v1/ws/drafts?token=<access_token>
```

**Server → Client events:**

```json
// Draft ready
{
  "type": "draft_ready",
  "draft_id": "uuid",
  "sender_name": "Jordan",
  "channel": "instagram_dm",
  "confidence": 0.88,
  "preview": "Hey Jordan! Yeah absolutely..."
}

// Batch ready
{
  "type": "batch_ready",
  "cluster_id": "uuid",
  "cluster_label": "workout routine question",
  "message_count": 142
}

// Surge detected
{
  "type": "surge_detected",
  "surge_ratio": 8.3,
  "mode": "crisis_mode"
}

// Proactive suggestion
{
  "type": "proactive_suggestion",
  "suggestion_count": 2
}
```

Falls back to FCM push notification when WebSocket is not connected.

---

## Abuse Reporting

### `POST /report/twin/{twin_id}`

```json
// Request
{
  "report_type": "impersonation",
  // "impersonation" | "harmful_content" | "non_consensual" | "fraud" | "spam"
  "severity": "high",
  "description": "This account is impersonating me without consent",
  "evidence_urls": ["https://example.com/screenshot.png"]
}

// Response 201
{
  "report_id": "uuid",
  "status": "open",
  "created_at": "2026-04-24T11:10:00Z",
  "sla_deadline": "2026-04-24T14:10:00Z"  // 3-hour SLA for high severity
}
```

---

## Standard Error Shape

All errors return this structure:

```json
{
  "error": {
    "code": "CONSENT_REQUIRED",
    "message": "Voice clone consent must be granted before uploading a recording",
    "field": "consent_type",    // null if not field-specific
    "docs_url": "https://docs.selph.ai/errors/CONSENT_REQUIRED"
  }
}
```

**Common error codes:**

| Code | HTTP | Meaning |
|---|---|---|
| `INVALID_INPUT` | 400 | Validation failure — `field` specifies which field |
| `UNAUTHORIZED` | 401 | Missing or invalid access token |
| `FORBIDDEN` | 403 | Valid token but insufficient permissions |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `CONFLICT` | 409 | Resource already exists or state conflict |
| `GONE` | 410 | Resource existed but has expired (e.g., draft) |
| `CONSENT_REQUIRED` | 403 | Consent for this action has not been granted |
| `RATE_LIMITED` | 429 | Too many requests — `Retry-After` header set |
| `INTERNAL_ERROR` | 500 | Server error — safe to retry with exponential backoff |

---

## Rate Limits

| Endpoint Group | Limit | Window |
|---|---|---|
| `/auth/*` | 10 requests | 1 minute |
| `/drafts/*` | 100 requests | 1 minute |
| `/identity/*` | 60 requests | 1 minute |
| `/biometric/*` | 5 requests | 1 hour |
| `/webhooks/*` | 1000 requests | 1 minute |
| All others | 200 requests | 1 minute |

Rate limit headers returned on every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1745489400
```

---

## Versioning

- Current version: `v1`
- Version is in the URL path: `/v1/...`
- Breaking changes → new version (`v2`)
- Non-breaking additions → no version bump
- Deprecation notice: 6-month window before removing old version

---

*Status: API Design v1.0 — All endpoints defined for Phase 0–5 build*
