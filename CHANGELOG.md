# Changelog

All notable changes to this project are documented in this file.

## [0.9.0] - Unreleased

### Added
- Phase 8 Twin Quality Summary API:
	- `GET /v1/twin/quality-summary`
- Phase 8 Weekly Digest Summary API:
	- `GET /v1/twin/weekly-digest`
- Phase 8 Onboarding Status API:
	- `GET /v1/identity/onboarding/status`
- Phase 8 Referral System foundation:
	- `POST /v1/referrals/invite`
	- `POST /v1/referrals/accept`
	- `GET /v1/referrals/summary`
	- migration `004_phase8_referral_foundation`
- Phase 8 Performance Summary API for draft latency target tracking:
	- `GET /v1/twin/performance-summary`

### Changed
- `/ready` now includes database probe and structured readiness checks.
- `/ready` now validates production JWT secret safety before reporting ready.
- `/ready` now validates feature dependency configuration for:
	- Instagram OAuth/webhook settings
	- Gmail OAuth/PubSub settings
	- ElevenLabs voice provider API key when enabled
	- HeyGen avatar provider API key when enabled

### Fixed
- Referral acceptance now blocks self-referral code claims.
- Referral acceptance now blocks second-user claims for already-accepted codes.

### Validation
- Endpoint and full backend suites remain green through stacked Phase 8 PRs.
- Latest observed full backend run after Phase 8 hardening: `261 passed`.

## [0.7.1] - 2026-04-28

### Added
- Phase 6 voice provider foundation and registry.
- Voice consent and enrollment APIs.
- Draft voice generation queue and status APIs.
- Phase 7 avatar execution plan document.
- Optional Gmail webhook shared-secret protection via X-Webhook-Token.

### Changed
- OAuth state for channel callbacks is signed and purpose-bound.
- LiteLLM import is lazy-loaded in twin engine to avoid startup warning noise.
- Twin stats schema now explicitly allows model_breakdown field name in Pydantic v2.
- Instagram webhook ingestion caches page-to-user lookups per request.

### Security
- Production startup now enforces strong JWT secret policy.
- Production-only auth rate limiting introduced for signup and login endpoints.

### Validation
- Backend test suite passes fully after these changes.
