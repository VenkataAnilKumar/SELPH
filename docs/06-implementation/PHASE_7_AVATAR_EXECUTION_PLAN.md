# SELPH Phase 7 Avatar Clone Execution Plan

Date: 2026-04-28
Owner: Engineering
Status: Ready to Execute

## Objective

Ship Phase 7 Avatar Clone as a safe, reversible extension of the existing text and voice pipeline, with clear quality gates before production rollout.

## Scope

In scope:
- Avatar consent and enrollment flow
- Avatar provider abstraction (default self-hosted, optional managed provider)
- Draft-to-video generation workflow
- Transparent mode verification overlay
- Audit and moderation checks before delivery
- Test coverage for core happy and failure paths

Out of scope:
- Real-time avatar calls
- Multi-language lip-sync optimization
- Enterprise admin controls

## Architecture Additions

Backend additions:
- app/avatar/base.py
- app/avatar/registry.py
- app/avatar/providers/linly.py
- app/avatar/providers/heygen.py
- app/tasks/avatar_synthesis.py
- app/routers/avatar.py
- app/schemas/avatar.py
- app/services/avatar.py

Data model additions:
- identity_profiles:
  - avatar_provider
  - avatar_model_id
  - avatar_sample_url
  - avatar_consent
  - avatar_consent_at
- drafts:
  - avatar_status
  - avatar_video_url
  - avatar_provider
  - avatar_model_id
  - avatar_error

## Rollout Sequence

1. Foundation and schema migration
- Add avatar provider interface and provider registry.
- Add DB migration for identity and draft avatar fields.
- Add feature flag: feature_avatar_clone.

2. Consent and enrollment endpoints
- Add endpoints to grant/revoke avatar consent.
- Add endpoint to enroll avatar profile after consent.
- Add endpoint to clear avatar profile.

3. Draft video generation endpoints
- Add POST endpoint to queue avatar generation for approved or edited drafts.
- Add GET endpoint for avatar generation status.
- Enforce ownership, consent, and draft status checks.

4. Safety and transparency controls
- Apply moderation gate before video synthesis.
- Apply transparent verification overlay metadata.
- Persist full audit events for queue, generation, and failure.

5. Provider and failure hardening
- Implement deterministic mock path for tests.
- Add retry and error normalization for provider failures.
- Ensure idempotent status transitions for repeated queue requests.

## Acceptance Criteria

- User can enable avatar consent and enroll an avatar profile.
- Avatar generation can be queued for approved and edited drafts.
- Status endpoint returns queued, processing, completed, or failed.
- Generated video URL is persisted and returned to user.
- Transparent mode metadata is applied and auditable.
- Full backend tests pass with no warnings.

## Test Plan

Unit tests:
- Provider registry selection and unknown-provider errors.
- Avatar task behavior for disabled feature, consent missing, provider unavailable.

Integration tests:
- Consent and enrollment endpoints.
- Queue and status endpoints.
- Ownership and invalid-state rejection paths.

Regression tests:
- Existing auth, identity, draft, and channels tests remain green.

## Risk Register

1. Provider instability
- Mitigation: provider abstraction, retries, graceful fail state.

2. Unsafe impersonation misuse
- Mitigation: explicit consent, transparent mode watermark, audit trail.

3. Latency spikes on generation
- Mitigation: queue-based async pipeline and status polling.

4. Data retention concerns for media
- Mitigation: storage lifecycle policy and explicit delete flow.

## Execution Checklist

- [ ] Migration created and reversible
- [ ] Avatar provider interface and registry implemented
- [ ] Consent and enrollment endpoints implemented
- [ ] Draft queue and status endpoints implemented
- [ ] Avatar synthesis task implemented
- [ ] Audit and safety checks implemented
- [ ] Test suite passes with no warnings
- [ ] Feature flag rollout documented

## Branching and Delivery

Branch: feature/phase7-planning
Next implementation branch: feature/phase7-avatar-pr-a
Delivery model: stacked PRs (A foundation, B consent/enrollment, C generation/status)
