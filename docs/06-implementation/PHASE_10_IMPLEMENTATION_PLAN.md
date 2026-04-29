# SELPH — Phase 10 Implementation Plan

> Version: 1.0
> Created: 2026-04-28
> Author: Engineering
> Scope: Features 3–10 from SELPH_Feature-Expansion-Spec.md
> Status: Ready to Execute
> Reference: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md)

---

## Context

Phases 0–9 are complete. All MVP backend infrastructure is operational:
- Auth, Twin Engine, Identity, Channels (Instagram + Gmail), Safety Layer
- Voice Clone (Phase 6), Avatar Clone (Phase 7), Beta Quality Dashboard (Phase 8)
- Feature Expansion Phase 9: Twin Briefings, VIP Sender Tiers, Batch Pattern Approval + Render Pipeline

**280 backend tests passing. Main branch clean at `645a842`.**

Phase 10 covers the remaining 7 features from the expansion spec, organised into 3 sub-phases by dependency order and delivery value.

---

## Phase Map

| Sub-Phase | Features | Estimated Slices | Priority |
|---|---|---|---|
| 10-A | Proactive Twin (Feature 3) | 4 | Highest |
| 10-A | Crisis / Surge Mode (Feature 5) | 3 | Highest |
| 10-B | Multi-Identity Profiles (Feature 6) | 4 | High |
| 10-B | Style Evolution / Identity Refresh (Feature 7) | 3 | High |
| 10-C | Twin Verification Public API (Feature 8) | 3 | Medium |
| 10-C | Privacy / On-Device Processing Mode (Feature 9) | 2 | Medium |
| 10-C | Twin-to-Twin Protocol (Feature 10) | 4 | Low |

---

## Sub-Phase 10-A — Autonomy & Safety (Priority: Ship First)

### Feature 3 — Proactive Twin

**Problem:** The twin only reacts. It has full visibility of the user's inbox and relationship graph but does nothing without being triggered.

**What ships:**
- Background signal scanner (runs every 6 hours per user via Celery beat)
- Suggestion types: cold_relationship, open_thread, deal_signal, follow_up
- `proactive_suggestions` and `proactive_preferences` tables
- `GET /v1/suggestions` and `POST /v1/suggestions/{id}/act` endpoints
- Per-user opt-in preference controls
- Push notification: "Your twin spotted N follow-up opportunities"

#### Slice 10-A-1 — Proactive Suggestions Data Model + Service

**Files to create/modify:**

```
src/backend/app/models/proactive_suggestion.py     NEW
src/backend/app/models/proactive_preference.py     NEW
src/backend/app/models/__init__.py                 UPDATE — add new models
src/backend/app/schemas/proactive.py               NEW
src/backend/app/schemas/__init__.py                UPDATE
src/backend/migrations/versions/
  008_phase10a_proactive_suggestions.py            NEW
```

**Model: `proactive_suggestions`**

```python
class ProactiveSuggestion(BaseModel):
    __tablename__ = "proactive_suggestions"

    user_id          = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    suggestion_type  = Column(String(50), nullable=False)   # cold_relationship, open_thread, deal_signal, follow_up, thank_you
    contact_id       = Column(String(200), nullable=True)
    signal_summary   = Column(Text, nullable=False)
    draft_message    = Column(Text, nullable=False)
    urgency_score    = Column(Float, nullable=False, default=0.5)
    value_score      = Column(Float, nullable=False, default=0.5)
    status           = Column(String(50), nullable=False, default="pending")
    snoozed_until    = Column(DateTime, nullable=True)
    acted_at         = Column(DateTime, nullable=True)
```

**Model: `proactive_preferences`**

```python
class ProactivePreference(BaseModel):
    __tablename__ = "proactive_preferences"

    user_id                  = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    enabled                  = Column(Boolean, nullable=False, default=True)
    enabled_types            = Column(JSON, nullable=False, default=["cold_relationship", "open_thread", "deal_signal"])
    cold_threshold_days      = Column(Integer, nullable=False, default=14)
    open_thread_hours        = Column(Integer, nullable=False, default=48)
    max_suggestions_per_day  = Column(Integer, nullable=False, default=5)
```

**Schemas: `proactive.py`**

```python
class ProactiveSuggestionResponse(BaseModel):
    id: str
    suggestion_type: str
    contact_id: Optional[str]
    signal_summary: str
    draft_message: str
    urgency_score: float
    value_score: float
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SuggestionActRequest(BaseModel):
    action: str             # approve, dismiss, never, snooze
    edited_message: Optional[str] = None
    snooze_days: int = 30

class ProactivePreferenceUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    enabled_types: Optional[list[str]] = None
    cold_threshold_days: Optional[int] = None
    open_thread_hours: Optional[int] = None
    max_suggestions_per_day: Optional[int] = None
```

---

#### Slice 10-A-2 — Signal Scanner Service

**Files to create/modify:**

```
src/backend/app/services/proactive.py              NEW
```

**Service: `ProactiveService`**

Key methods:
- `scan_signals(db, user_id)` — detects all signal types for a user
- `_detect_cold_relationships(db, user_id, threshold_days)` — finds contacts with no reply in N days
- `_detect_open_threads(db, user_id, threshold_hours)` — finds messages with no draft after N hours
- `_detect_deal_signals(db, user_id)` — keyword/pattern matching on incoming messages (collab, sponsorship, partnership, rate, deal)
- `_detect_follow_ups(db, user_id)` — conversations that ended without resolution marker
- `create_suggestion(db, user_id, type, contact_id, signal_summary, draft_message, urgency, value)` — creates suggestion row
- `list_suggestions(db, user_id, status, limit)` — paginated list
- `act_on_suggestion(db, suggestion_id, user_id, action, edited_message, snooze_days)` — handles approve/dismiss/never/snooze
- `get_or_create_preferences(db, user_id)` — returns preferences, creating defaults if absent
- `update_preferences(db, user_id, updates)` — partial update

**Daily limit enforcement:**

```python
def _under_daily_limit(db, user_id, prefs) -> bool:
    today_count = db.query(ProactiveSuggestion).filter(
        ProactiveSuggestion.user_id == user_id,
        ProactiveSuggestion.created_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0),
    ).count()
    return today_count < prefs.max_suggestions_per_day
```

---

#### Slice 10-A-3 — Celery Task + Router

**Files to create/modify:**

```
src/backend/app/tasks/proactive_scan.py            NEW
src/backend/app/routers/proactive.py               NEW
src/backend/app/main.py                            UPDATE — include proactive router
```

**Celery task:**

```python
@celery_app.task(name="tasks.run_proactive_scan")
def run_proactive_scan(user_id: str) -> dict:
    """Run proactive signal scan for one user. Scheduled via Celery beat every 6 hours."""
    db = next(get_db())
    try:
        prefs = ProactiveService.get_or_create_preferences(db, user_id)
        if not prefs.enabled:
            return {"user_id": user_id, "skipped": True, "reason": "disabled"}
        suggestions = ProactiveService.scan_signals(db, user_id)
        return {"user_id": user_id, "suggestions_created": len(suggestions)}
    finally:
        db.close()
```

**Celery beat schedule addition in `celery_app.py`:**

```python
beat_schedule={
    "proactive-scan-every-6h": {
        "task": "tasks.run_proactive_scan",
        "schedule": crontab(minute=0, hour="*/6"),
        "args": [],   # per-user fan-out via chord
    }
}
```

**Router endpoints:**

```
GET    /v1/proactive/suggestions              — list pending suggestions (paginated)
POST   /v1/proactive/suggestions/{id}/act    — approve / dismiss / never / snooze
GET    /v1/proactive/preferences              — get current preferences
PATCH  /v1/proactive/preferences              — update preferences
POST   /v1/proactive/scan                    — manual trigger (dev + power users)
```

---

#### Slice 10-A-4 — Tests

**File:**

```
src/backend/tests/test_proactive.py            NEW
```

**Test coverage (target ≥ 30 tests):**

- `TestProactiveService`
  - scan creates cold_relationship suggestion when contact silent > threshold
  - scan creates open_thread suggestion when message unanswered > threshold
  - scan respects daily limit (does not exceed max_suggestions_per_day)
  - scan respects disabled preference (creates 0 suggestions)
  - scan filters disabled_types from results
  - approve action sets status=approved, records acted_at
  - dismiss action sets status=dismissed, sets snoozed_until
  - never action sets status=never (persists permanently)
  - get_or_create_preferences returns defaults on first call
  - update_preferences partial update preserves other fields

- `TestProactiveEndpoints`
  - GET /suggestions returns only pending suggestions for current user
  - GET /suggestions filters by status query param
  - POST /suggestions/{id}/act approve returns 200
  - POST /suggestions/{id}/act with edited_message uses edited text
  - POST /suggestions/{id}/act for other user returns 403
  - POST /suggestions/nonexistent/act returns 404
  - GET /preferences returns defaults for new user
  - PATCH /preferences updates enabled flag
  - POST /scan creates suggestions (integration)

---

### Feature 5 — Crisis / Surge Mode

**Problem:** Viral events and controversies require immediate twin behavior change. Normal routing into a crisis is dangerous.

**What ships:**
- Surge detection algorithm (volume + sentiment)
- `surge_events` and `crisis_templates` tables
- Twin operating state machine (normal → alert → crisis → paused)
- Crisis mode enforcement in draft generation task
- `GET /v1/twin/surge-status`, `POST /v1/twin/crisis/*` endpoints
- Auto-resume when volume normalizes

#### Slice 10-A-5 — Surge Detection + Data Model

**Files:**

```
src/backend/app/models/surge_event.py              NEW
src/backend/app/models/crisis_template.py          NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/schemas/crisis.py                  NEW
src/backend/app/schemas/__init__.py                UPDATE
src/backend/migrations/versions/
  009_phase10a_crisis_surge.py                     NEW
```

**Model: `surge_events`**

```python
class SurgeEvent(BaseModel):
    __tablename__ = "surge_events"

    user_id         = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    trigger_type    = Column(String(50), nullable=False)   # volume_surge, sentiment_surge, manual, keyword
    trigger_value   = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    baseline_rate   = Column(Float, nullable=True)
    peak_rate       = Column(Float, nullable=True)
    mode_activated  = Column(String(50), nullable=False)   # crisis_alert, crisis_mode, manual_pause
    resolved_at     = Column(DateTime, nullable=True)
    resolution_type = Column(String(50), nullable=True)    # manual_resume, auto_normalized, user_dismissed
```

**Model: `crisis_templates`**

```python
class CrisisTemplate(BaseModel):
    __tablename__ = "crisis_templates"

    user_id       = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    label         = Column(String(100), nullable=False)
    content       = Column(Text, nullable=False)
    template_type = Column(String(50), nullable=False)   # acknowledge, clarify, appreciation, custom
    approved_at   = Column(DateTime, nullable=False)
    last_used_at  = Column(DateTime, nullable=True)
```

**Also update `users` or `twins` table** to carry `twin_operating_mode`:

```python
# Add to Twin model via migration 009:
# twin_operating_mode VARCHAR(50) NOT NULL DEFAULT 'normal'
# Allowed: normal, crisis_alert, crisis_mode, manual_pause
```

---

#### Slice 10-A-6 — Surge Service + Crisis Enforcement

**Files:**

```
src/backend/app/services/crisis.py                 NEW
src/backend/app/tasks/surge_check.py               NEW
src/backend/app/tasks/draft_generation.py          UPDATE — enforce crisis state
```

**Service: `CrisisService`**

Key methods:
- `check_surge(db, user_id)` — rolling 1-hour rate vs 7-day baseline; returns `SurgeStatus`
- `activate_crisis_mode(db, user_id, trigger_type, mode)` — creates `SurgeEvent`, updates twin operating mode
- `resolve_crisis(db, user_id, resolution_type)` — marks event resolved, restores normal mode
- `get_active_surge_event(db, user_id)` — returns unresolved event or None
- `list_crisis_templates(db, user_id)` — returns user's templates
- `create_crisis_template(db, user_id, ...)` — validates ≤ 5 templates per user
- `delete_crisis_template(db, user_id, template_id)`

**Draft generation enforcement (update `draft_generation.py`):**

```python
def run_twin_pipeline(user_id, message_id):
    mode = get_twin_operating_mode(db, user_id)

    if mode == "manual_pause":
        return {"skipped": True, "reason": "twin_paused"}

    if mode == "crisis_mode":
        # Only pre-approved crisis templates can be used — no LLM generation
        return {"skipped": True, "reason": "crisis_mode_active", "use_crisis_template": True}

    if mode == "crisis_alert":
        # Generate draft but force-route to user regardless of confidence
        draft = generate_draft(...)
        draft.force_review = True
        return draft

    # Normal mode — standard routing
    ...
```

**Celery beat: surge check every 15 minutes per active user.**

---

#### Slice 10-A-7 — Crisis Router + Tests

**Files:**

```
src/backend/app/routers/crisis.py                  NEW
src/backend/app/main.py                            UPDATE
src/backend/tests/test_crisis.py                   NEW
```

**Router endpoints:**

```
GET    /v1/twin/surge-status                  — current mode + active event if any
POST   /v1/twin/crisis/activate               — manual crisis mode activation
POST   /v1/twin/crisis/resolve                — manual resume
GET    /v1/twin/crisis/templates              — list crisis templates
POST   /v1/twin/crisis/templates              — create crisis template
DELETE /v1/twin/crisis/templates/{id}         — delete template
```

**Test coverage (target ≥ 20 tests):**

- `TestCrisisService`
  - check_surge returns normal when message rate is baseline
  - check_surge triggers volume_surge at ≥ 5x baseline
  - activate_crisis_mode creates SurgeEvent and updates twin mode
  - resolve_crisis marks event resolved and restores normal mode
  - create_crisis_template enforces max-5 limit
  - draft_generation returns skipped when mode=manual_pause
  - draft_generation returns force_review=True when mode=crisis_alert

- `TestCrisisEndpoints`
  - GET /surge-status returns normal for new user
  - POST /crisis/activate sets mode to crisis_mode
  - POST /crisis/resolve restores normal mode
  - POST /crisis/templates creates template
  - POST /crisis/templates rejects 6th template with 409
  - DELETE /crisis/templates/{id} removes template

---

## Sub-Phase 10-B — Identity Depth

### Feature 6 — Multi-Identity Profiles

**Problem:** Users with multiple public identities (creator + professional, brand + personal) get one-size-fits-all twin behavior that is wrong for each context.

**What ships:**
- Multiple named identity profiles per user
- Channel-to-profile routing table
- Profile selection logic in twin engine
- `POST /v1/identity/profiles`, `GET /v1/identity/profiles`, channel mapping CRUD

#### Slice 10-B-1 — Multi-Profile Data Model

**Files:**

```
src/backend/app/models/identity_profile.py         UPDATE — add profile_name, profile_type, is_primary, is_active
src/backend/app/models/channel_profile_mapping.py  NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/schemas/identity.py                UPDATE — add multi-profile schemas
src/backend/migrations/versions/
  010_phase10b_multi_identity_profiles.py          NEW
```

**Migration adds to `identity_profiles`:**

```sql
ALTER TABLE identity_profiles
  ADD COLUMN profile_name  VARCHAR(100) NOT NULL DEFAULT 'Default',
  ADD COLUMN profile_type  VARCHAR(50)  NOT NULL DEFAULT 'personal_brand',
  ADD COLUMN is_primary    BOOLEAN      NOT NULL DEFAULT false,
  ADD COLUMN is_active     BOOLEAN      NOT NULL DEFAULT true;
```

**New model: `channel_profile_mappings`**

```python
class ChannelProfileMapping(BaseModel):
    __tablename__ = "channel_profile_mappings"

    user_id          = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    profile_id       = Column(String, ForeignKey("identity_profiles.id"), nullable=False)
    channel          = Column(String(50), nullable=False)
    platform_account = Column(String(200), nullable=True)
    priority         = Column(Integer, nullable=False, default=1)
    # UNIQUE(user_id, channel, platform_account)
```

---

#### Slice 10-B-2 — Profile Service + Router

**Files:**

```
src/backend/app/services/identity.py               UPDATE — multi-profile methods
src/backend/app/routers/identity.py                UPDATE — multi-profile endpoints
```

**Service additions:**

- `create_profile(db, user_id, profile_name, profile_type)` — max 5 profiles per user
- `list_profiles(db, user_id)` — all active profiles
- `set_primary_profile(db, user_id, profile_id)` — swaps is_primary flag
- `deactivate_profile(db, user_id, profile_id)` — soft-delete (keeps history)
- `upsert_channel_mapping(db, user_id, profile_id, channel, platform_account)`
- `delete_channel_mapping(db, user_id, channel, platform_account)`
- `resolve_profile_for_channel(db, user_id, channel, platform_account)` — selection logic

**Router endpoints:**

```
GET    /v1/identity/profiles                        — list all profiles
POST   /v1/identity/profiles                        — create profile
PATCH  /v1/identity/profiles/{profile_id}           — rename / change type
DELETE /v1/identity/profiles/{profile_id}           — deactivate
POST   /v1/identity/profiles/{profile_id}/primary   — set as primary
GET    /v1/identity/channel-mappings                — list channel mappings
PUT    /v1/identity/channel-mappings                — upsert mapping
DELETE /v1/identity/channel-mappings/{channel}      — remove mapping
```

**Twin engine integration:**

```python
# twin_engine.py — update context builder
profile = IdentityService.resolve_profile_for_channel(
    db, user_id, message.channel, message.platform_account
)
context.identity_profile = profile
```

---

#### Slices 10-B-3 + 10-B-4 — Style Evolution

### Feature 7 — Style Evolution / Identity Refresh

**Problem:** Users change over time. The twin was calibrated in 2024; by 2026 their communication style has shifted. Drift correction (Phase 8) handles unintended drift. Style Evolution handles intentional change.

**What ships:**
- Style divergence score computation
- Quarterly checkpoint scheduler
- Style Delta Report generation
- User-controlled update flow with partial dimension selection
- `style_checkpoints` table + endpoints

#### Slice 10-B-3 — Divergence Computation + Checkpoint Model

**Files:**

```
src/backend/app/models/style_checkpoint.py         NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/services/style_evolution.py        NEW
src/backend/app/schemas/style.py                   NEW
src/backend/migrations/versions/
  011_phase10b_style_checkpoints.py                NEW
```

**Model: `style_checkpoints`**

```python
class StyleCheckpoint(BaseModel):
    __tablename__ = "style_checkpoints"

    user_id             = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    profile_id          = Column(String, ForeignKey("identity_profiles.id"), nullable=False)
    trigger_type        = Column(String(50), nullable=False)   # automatic, manual
    divergence_score    = Column(Float, nullable=False)
    delta_report        = Column(JSON, nullable=False)
    sample_old          = Column(Text, nullable=False)
    sample_new          = Column(Text, nullable=False)
    decision            = Column(String(50), nullable=True)    # update, keep, partial
    updated_dimensions  = Column(JSON, nullable=True)
    decided_at          = Column(DateTime, nullable=True)
```

**Service: `StyleEvolutionService`**

Key methods:
- `compute_divergence(db, user_id, profile_id)` — average cosine distance between recent approved drafts and identity embedding centroid; returns float 0.0–1.0
- `generate_delta_report(db, user_id, profile_id)` — builds side-by-side dimension comparison dict
- `create_checkpoint(db, user_id, profile_id, trigger_type)` — creates checkpoint row with delta report
- `apply_checkpoint_decision(db, checkpoint_id, user_id, decision, updated_dimensions)` — applies update, keep, or partial; archives old profile version on update
- `get_pending_checkpoints(db, user_id)` — checkpoints awaiting decision

---

#### Slice 10-B-4 — Checkpoint Scheduler + Router

**Files:**

```
src/backend/app/tasks/style_evolution.py           NEW
src/backend/app/routers/style.py                   NEW
src/backend/app/main.py                            UPDATE
src/backend/tests/test_style_evolution.py          NEW
```

**Celery beat: quarterly divergence check per active user (every 90 days).**

**Router endpoints:**

```
GET    /v1/twin/style/checkpoints                   — list pending checkpoints
GET    /v1/twin/style/checkpoints/{id}              — get one checkpoint with delta report
POST   /v1/twin/style/checkpoints/{id}/decide       — apply decision (update/keep/partial)
POST   /v1/twin/style/refresh                       — manual divergence check trigger
```

---

## Sub-Phase 10-C — Trust, Privacy & Coordination

### Feature 8 — Twin Verification Public API

**Problem:** Any message can claim to be from a SELPH twin. Without a public verification endpoint, the "Powered by SELPH" badge is unverifiable and therefore untrusted.

**What ships:**
- RSA key pair generation per twin at creation
- Message HMAC-SHA256 signing in draft pipeline
- `twin_certificates` and `verification_log` tables
- Public `GET /verify/{twin_id}/{message_hash}` endpoint (no auth required)
- Public certificate page metadata (`GET /verify/{twin_id}`)
- `X-SELPH-Twin-ID` + `X-SELPH-Signature` headers on draft outputs

#### Slice 10-C-1 — Certificate Issuance

**Files:**

```
src/backend/app/models/twin_certificate.py         NEW
src/backend/app/models/verification_log.py         NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/services/verification.py           NEW
src/backend/migrations/versions/
  012_phase10c_twin_certificates.py                NEW
```

**Model: `twin_certificates`**

```python
class TwinCertificate(BaseModel):
    __tablename__ = "twin_certificates"

    user_id         = Column(String, ForeignKey("users.id"), nullable=False)
    twin_public_id  = Column(String(50), unique=True, nullable=False, index=True)  # twn_xxxxx
    public_key      = Column(Text, nullable=False)
    private_key_ref = Column(String(200), nullable=False)   # encrypted ref; raw key never stored
    issued_at       = Column(DateTime, nullable=False)
    expires_at      = Column(DateTime, nullable=False)
    revoked_at      = Column(DateTime, nullable=True)
    revoke_reason   = Column(String(200), nullable=True)
```

**Service: `VerificationService`**

- `issue_certificate(db, user_id, twin_id)` — generate RSA-2048 key pair, encrypt private key with SELPH master key (AES-256), store public key in DB, return twin_public_id
- `sign_message(private_key_ref, message_content, timestamp)` — HMAC-SHA256 signature
- `verify_message(db, twin_public_id, message_hash, signature, timestamp)` — verify signature; return VerificationResult
- `revoke_certificate(db, user_id, reason)` — marks certificate revoked; all future verifications return invalid
- `get_certificate_metadata(db, twin_public_id)` — public certificate info (no private key)

---

#### Slice 10-C-2 — Verification Router + Draft Integration

**Files:**

```
src/backend/app/routers/verification.py            NEW
src/backend/app/main.py                            UPDATE
src/backend/app/services/draft.py                  UPDATE — attach signature to approved drafts
```

**Router endpoints (public — no auth required):**

```
GET  /verify/{twin_id}                   — get public certificate metadata
GET  /verify/{twin_id}/{message_hash}    — verify a message signature
```

**Private endpoints (authenticated):**

```
GET  /v1/twin/certificate                — get my certificate details
POST /v1/twin/certificate/revoke         — revoke my certificate
```

**Draft approval integration:**

```python
# After user approves a draft:
cert = VerificationService.get_certificate(db, user_id)
if cert and not cert.revoked_at:
    signature = VerificationService.sign_message(
        cert.private_key_ref, draft.content, datetime.now(UTC)
    )
    draft.selph_signature = signature
    draft.selph_twin_id = cert.twin_public_id
```

---

#### Slice 10-C-3 — Verification Tests

**File:**

```
src/backend/tests/test_verification.py             NEW
```

**Test coverage (target ≥ 15 tests):**

- Certificate is auto-issued when twin is created
- Sign + verify round-trip returns valid=True
- Tampered message_hash returns valid=False with reason=signature_mismatch
- Revoked certificate returns valid=False with reason=certificate_revoked
- GET /verify/{twin_id} returns public metadata without exposing private key
- GET /verify/{twin_id}/{hash} returns valid result without auth
- POST /v1/twin/certificate/revoke updates certificate and all future verifications return invalid

---

### Feature 9 — Privacy / On-Device Processing Mode

**Problem:** Enterprise and privacy-focused users will not upload identity data to a cloud service.

**What ships:**
- Processing mode setting per user (cloud / hybrid / on_device)
- `user_privacy_settings` table
- Feature gating in twin engine based on processing mode
- API to read and update privacy settings
- Capability check endpoint (is device eligible for on-device mode?)

#### Slice 10-C-4 — Privacy Settings Model + Enforcement

**Files:**

```
src/backend/app/models/user_privacy_settings.py    NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/schemas/privacy.py                 NEW
src/backend/app/schemas/__init__.py                UPDATE
src/backend/app/services/privacy.py                NEW
src/backend/app/routers/privacy.py                 NEW
src/backend/app/main.py                            UPDATE
src/backend/app/tasks/draft_generation.py          UPDATE
src/backend/migrations/versions/
  013_phase10c_privacy_settings.py                 NEW
```

**Model: `user_privacy_settings`**

```python
class UserPrivacySettings(BaseModel):
    __tablename__ = "user_privacy_settings"

    user_id              = Column(String, ForeignKey("users.id"), primary_key=True)
    processing_mode      = Column(String(20), nullable=False, default="cloud")
    on_device_capable    = Column(Boolean, nullable=False, default=False)
    voice_clone_enabled  = Column(Boolean, nullable=False, default=False)
    avatar_enabled       = Column(Boolean, nullable=False, default=False)
    cloud_sync_scope     = Column(String(50), nullable=False, default="full")
```

**Draft generation enforcement:**

```python
privacy = PrivacyService.get_settings(db, user_id)

if privacy.processing_mode == "on_device":
    # On-device drafts must always be reviewed — never auto-approved
    draft.force_review = True
    draft.generation_source = "on_device"
    draft.confidence_score = None   # No confidence scoring without cloud LLM

if privacy.processing_mode in ("on_device", "hybrid"):
    # Voice and avatar features unavailable
    if requires_voice_or_avatar:
        return {"error": "feature_unavailable_in_privacy_mode"}
```

**Router endpoints:**

```
GET    /v1/privacy/settings          — get current privacy settings
PATCH  /v1/privacy/settings          — update processing mode, sync scope
POST   /v1/privacy/capability-check  — report device capability (from mobile app)
```

---

#### Slice 10-C-5 — Privacy Tests

**File:**

```
src/backend/tests/test_privacy.py                  NEW
```

**Test coverage (target ≥ 12 tests):**

- Default settings are cloud mode
- PATCH /privacy/settings updates processing_mode
- on_device mode sets force_review=True on all generated drafts
- on_device mode returns feature_unavailable for voice/avatar requests
- capability-check endpoint updates on_device_capable flag
- hybrid mode allows draft generation but blocks voice/avatar
- User cannot set on_device mode when on_device_capable=False

---

### Feature 10 — Twin-to-Twin Protocol (T2T)

**Problem:** When two SELPH users interact, both twins work independently and route everything back to their humans. Coordinated negotiation (scheduling, availability, introductions) would reduce human round-trips.

**What ships:**
- T2T handshake detection (SELPH watermark recognition)
- `t2t_sessions` table
- Negotiation types: scheduling, availability, introduction
- Both-human approval gate before any outcome is committed
- Session expiry (48 hours)
- Opt-in per user

#### Slice 10-C-6 — T2T Session Model

**Files:**

```
src/backend/app/models/t2t_session.py              NEW
src/backend/app/models/__init__.py                 UPDATE
src/backend/app/schemas/t2t.py                     NEW
src/backend/migrations/versions/
  014_phase10c_t2t_sessions.py                     NEW
```

**Model: `t2t_sessions`**

```python
class T2TSession(BaseModel):
    __tablename__ = "t2t_sessions"

    initiating_twin    = Column(String(50), nullable=False)
    receiving_twin     = Column(String(50), nullable=False)
    session_type       = Column(String(50), nullable=False)
    status             = Column(String(50), nullable=False, default="handshake")
    negotiation_log    = Column(JSON, nullable=False, default=list)
    proposal           = Column(JSON, nullable=True)
    initiator_approved = Column(Boolean, nullable=True)
    receiver_approved  = Column(Boolean, nullable=True)
    started_at         = Column(DateTime, nullable=False)
    completed_at       = Column(DateTime, nullable=True)
    expires_at         = Column(DateTime, nullable=False)
```

---

#### Slice 10-C-7 — T2T Service + Handshake

**Files:**

```
src/backend/app/services/t2t.py                    NEW
src/backend/app/tasks/t2t_negotiation.py           NEW
```

**Service: `T2TService`**

- `detect_t2t_capable(message_content)` — scans message for SELPH watermark / T2T probe header
- `initiate_session(db, initiating_twin_id, receiving_twin_id, session_type)` — creates session in handshake state
- `respond_to_handshake(db, session_id, accept, capabilities)` — receiving twin accepts/rejects
- `add_negotiation_turn(db, session_id, turn)` — appends to negotiation_log
- `propose_outcome(db, session_id, proposal)` — sets proposal, transitions to proposed state
- `record_approval(db, session_id, twin_id, approved)` — records per-twin approval; when both approved → completed
- `expire_stale_sessions(db)` — marks sessions past expires_at as expired

---

#### Slices 10-C-8 + 10-C-9 — T2T Router + Tests

**Files:**

```
src/backend/app/routers/t2t.py                     NEW
src/backend/app/main.py                            UPDATE
src/backend/tests/test_t2t.py                      NEW
```

**Router endpoints:**

```
GET    /v1/t2t/sessions                     — list my active T2T sessions
GET    /v1/t2t/sessions/{id}                — get session + negotiation log
POST   /v1/t2t/sessions/{id}/approve        — approve proposed outcome
POST   /v1/t2t/sessions/{id}/reject         — reject and close session
POST   /v1/t2t/sessions/{id}/exit           — exit T2T mode (revert to standard routing)
```

**Test coverage (target ≥ 15 tests):**

- Handshake creates session in handshake state
- Rejection of handshake closes session
- add_negotiation_turn appends to log and preserves order
- propose_outcome transitions session to proposed
- Single approval keeps status=proposed
- Both approvals transition to completed
- Expired session cannot be approved
- exit T2T reverts routing to standard

---

## Full File Change Index

### New Models (8)

| File | Table | Slice |
|---|---|---|
| `models/proactive_suggestion.py` | proactive_suggestions | 10-A-1 |
| `models/proactive_preference.py` | proactive_preferences | 10-A-1 |
| `models/surge_event.py` | surge_events | 10-A-5 |
| `models/crisis_template.py` | crisis_templates | 10-A-5 |
| `models/channel_profile_mapping.py` | channel_profile_mappings | 10-B-1 |
| `models/style_checkpoint.py` | style_checkpoints | 10-B-3 |
| `models/twin_certificate.py` | twin_certificates | 10-C-1 |
| `models/user_privacy_settings.py` | user_privacy_settings | 10-C-4 |
| `models/t2t_session.py` | t2t_sessions | 10-C-6 |
| `models/verification_log.py` | verification_log | 10-C-1 |

### New Migrations (7)

| File | Slice |
|---|---|
| `008_phase10a_proactive_suggestions.py` | 10-A-1 |
| `009_phase10a_crisis_surge.py` | 10-A-5 |
| `010_phase10b_multi_identity_profiles.py` | 10-B-1 |
| `011_phase10b_style_checkpoints.py` | 10-B-3 |
| `012_phase10c_twin_certificates.py` | 10-C-1 |
| `013_phase10c_privacy_settings.py` | 10-C-4 |
| `014_phase10c_t2t_sessions.py` | 10-C-6 |

### New Services (7)

| File | Slice |
|---|---|
| `services/proactive.py` | 10-A-2 |
| `services/crisis.py` | 10-A-6 |
| `services/style_evolution.py` | 10-B-3 |
| `services/verification.py` | 10-C-1 |
| `services/privacy.py` | 10-C-4 |
| `services/t2t.py` | 10-C-7 |

### New Routers (6)

| File | Prefix | Slice |
|---|---|---|
| `routers/proactive.py` | /v1/proactive | 10-A-3 |
| `routers/crisis.py` | /v1/twin/crisis | 10-A-7 |
| `routers/style.py` | /v1/twin/style | 10-B-4 |
| `routers/verification.py` | /verify + /v1/twin/certificate | 10-C-2 |
| `routers/privacy.py` | /v1/privacy | 10-C-4 |
| `routers/t2t.py` | /v1/t2t | 10-C-8 |

### New Celery Tasks (3)

| File | Schedule | Slice |
|---|---|---|
| `tasks/proactive_scan.py` | Every 6 hours | 10-A-3 |
| `tasks/surge_check.py` | Every 15 minutes | 10-A-6 |
| `tasks/style_evolution.py` | Every 90 days | 10-B-4 |
| `tasks/t2t_negotiation.py` | On-demand | 10-C-7 |

### New Test Files (7)

| File | Target Tests | Slice |
|---|---|---|
| `tests/test_proactive.py` | ≥ 30 | 10-A-4 |
| `tests/test_crisis.py` | ≥ 20 | 10-A-7 |
| `tests/test_multi_identity.py` | ≥ 20 | 10-B-2 |
| `tests/test_style_evolution.py` | ≥ 15 | 10-B-4 |
| `tests/test_verification.py` | ≥ 15 | 10-C-3 |
| `tests/test_privacy.py` | ≥ 12 | 10-C-5 |
| `tests/test_t2t.py` | ≥ 15 | 10-C-9 |

**Total new tests: ≥ 127**
**Current test count: 280**
**Projected total: ≥ 407**

---

## Delivery Order (Recommended Sequence)

```
10-A-1  Proactive data model + service
10-A-2  Signal scanner
10-A-3  Celery task + router
10-A-4  Proactive tests  ← commit: feat(phase10): proactive twin foundation
10-A-5  Surge data model
10-A-6  Surge service + crisis enforcement
10-A-7  Crisis router + tests  ← commit: feat(phase10): crisis surge mode
10-B-1  Multi-profile data model
10-B-2  Profile service + router  ← commit: feat(phase10): multi-identity profiles
10-B-3  Divergence + checkpoint model + service
10-B-4  Checkpoint scheduler + router + tests  ← commit: feat(phase10): style evolution
10-C-1  Certificate model + service
10-C-2  Verification router + draft signing
10-C-3  Verification tests  ← commit: feat(phase10): twin verification api
10-C-4  Privacy settings + enforcement  ← commit: feat(phase10): privacy processing modes
10-C-5  Privacy tests
10-C-6  T2T session model
10-C-7  T2T service + handshake
10-C-8  T2T router + tests  ← commit: feat(phase10): twin-to-twin protocol
```

---

## Dependency Graph

```
Phase 9 complete (Briefings, Sender Tiers, Batch Approval, Render Pipeline)
          │
          ├── 10-A: Proactive Twin + Crisis Mode   (no deps on 10-B/10-C)
          │         │
          │         └── requires: Message model, Twin model, Celery beat
          │
          ├── 10-B: Multi-Identity + Style Evolution
          │         │
          │         └── requires: identity_profiles table, twin_engine context builder
          │
          └── 10-C: Verification + Privacy + T2T
                    │
                    ├── Verification: requires Twin model (twin_public_id addition)
                    ├── Privacy: requires draft_generation task
                    └── T2T: requires twin_certificates (depends on 10-C-1)
```

10-A and 10-B can be developed in parallel. 10-C-6 through 10-C-9 (T2T) depend on 10-C-1 (certificates).

---

## Definition of Done

Each slice is done when:

1. All models created with Alembic migration
2. Service methods covered by unit tests
3. Router endpoints covered by integration tests
4. All existing 280 tests continue to pass (`pytest src/backend/tests/ -q`)
5. Commit pushed to main with `feat(phase10):` prefix

Full Phase 10 is done when:
- ≥ 407 tests passing
- All 9 new router modules registered in `main.py`
- All 7 Alembic migrations applied cleanly from scratch
- No regressions in Phase 0–9 features
- Version tag `v1.0.0-rc` created
