# SELPH v0.9.0 (Draft)

Release Date: TBD
Tag: v0.9.0
Range: v0.8.0..main

## Summary
This release packages the Phase 8 beta-launch backend stack with creator-facing quality visibility, onboarding/drop-off diagnostics, referral growth foundations, performance SLO tracking, and rollout-readiness hardening.

## Highlights

### Added
- Twin quality dashboard API:
  - `GET /v1/twin/quality-summary`
- Weekly digest summary API:
  - `GET /v1/twin/weekly-digest`
- Onboarding completion and blocker API:
  - `GET /v1/identity/onboarding/status`
- Referral system APIs:
  - `POST /v1/referrals/invite`
  - `POST /v1/referrals/accept`
  - `GET /v1/referrals/summary`
- Referral persistence migration:
  - `004_phase8_referral_foundation`
- Draft-generation performance summary API:
  - `GET /v1/twin/performance-summary`

### Changed
- Readiness endpoint now validates:
  - database probe (`SELECT 1`)
  - production JWT safety
  - feature dependency config for Instagram, Gmail, ElevenLabs, and HeyGen
- Readiness endpoint now returns structured per-check status with failure reasons.

### Fixed
- Referral acceptance hardening:
  - self-referral code acceptance blocked
  - duplicate claim by second user blocked

## Included Stacked PRs
- #26 Phase 8 PR A: Twin Quality Summary API
- #27 Phase 8 PR B: Weekly Digest Summary API
- #28 Phase 8 PR C: Onboarding Status API
- #29 Phase 8 PR D: Referral System API
- #30 Phase 8 PR E: Performance Summary API
- #31 Phase 8 PR F: Referral Acceptance Hardening
- #32 Phase 8 PR G: Readiness Check Hardening
- #33 Phase 8 PR H: Feature Dependency Readiness Checks

## Validation
- Endpoint suite expanded and passing across all new APIs.
- Latest full backend regression after Phase 8 stack:
  - `261 passed`

## Release Notes
- This draft is intended for GitHub Release body text.
- Publish with tag `v0.9.0` after the Phase 8 stack is merged into `main`.
