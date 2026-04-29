# Changelog

All notable changes to this project are documented in this file.

## [1.0.0-rc] - 2026-04-28

### Added
- Phase 10 backend foundations delivered end-to-end:
	- Proactive Twin APIs and service layer (`/v1/proactive/*`)
	- Crisis/Surge controls (`/v1/twin/surge-status`, `/v1/twin/crisis/*`)
	- Multi-identity profile APIs (`/v1/identity/profiles`, `/v1/identity/channel-mappings`)
	- Style evolution checkpoint APIs (`/v1/twin/style/*`)
	- Verification APIs (`/verify/{twin_id}`, `/verify/{twin_id}/{message_hash}`, `/v1/twin/certificate*`)
	- Privacy processing mode APIs (`/v1/privacy/*`)
	- Twin-to-Twin protocol APIs (`/v1/t2t/*`)
- Phase 10 persistence and migration base:
	- New migration: `008_phase10_end_to_end_foundation`
	- New model families for proactive, crisis, identity variants, style checkpoints, certificates, privacy, and T2T sessions
- Phase 10 UI/API wiring in web and mobile dashboards:
	- Shared API client now exposes typed Phase 10 helpers
	- Dashboard action panels for proactive scan, crisis controls, privacy toggle, and certificate snapshot

### Changed
- Celery beat schedule expanded for proactive scans, surge checks, style refresh, and T2T maintenance.
- Draft approval/edit flow now attaches SELPH verification signature metadata.

### Fixed
- Alembic configuration now includes required `[alembic]` section header in [src/backend/alembic.ini](src/backend/alembic.ini).
- Migration runtime import path fixed in [src/backend/migrations/env.py](src/backend/migrations/env.py) so `alembic` resolves the backend package correctly.
- Migration smoke service image corrected from `pgvector/pgvector:pg16-latest` to `pgvector/pgvector:pg16` (commit `afc7582`).
- GitHub Actions service host changed to `127.0.0.1` to avoid IPv6 resolution issues in ubuntu-latest runners (commit `ec92db7`).
- Migration smoke switched to `npm run smoke:backend:migrate` from repo root to fix working directory mismatch (commit `e844978`).
- Alembic and pytest now invoked via `sys.executable -m` to avoid PATH resolution failures in CI (commit `da3d2ad`).
- DB readiness wait loop added (45 s, 1 s polling) with multi-host fallback probing so migration smoke waits for Postgres service to accept connections (commit `c4d8c99`).
- `CREATE EXTENSION IF NOT EXISTS vector` added as first statement of `001_initial_schema.upgrade()` so pgvector type is available before VECTOR-typed columns are created (commit `4f9fdc4`).
- `alembic_version.version_num` widened to `VARCHAR(256)` via `ALTER TABLE` at migration start — Alembic default of `VARCHAR(32)` is too short for descriptive revision IDs such as `005_phase9_twin_briefing_foundation` (commit `2da484c`).

### Validation — v1.0.0-rc (commit `2da484c`)
- GitHub Actions CI run `25088596786` — **all 4 jobs passed**:
  - Backend Tests: **success** (287 passed)
  - Web Tests: **success** (23 passed)
  - Mobile Tests: **success** (32 passed)
  - Migration Smoke: **success** (full schema applied + 7 smoke tests passed)
- Tag `v1.0.0-rc` points to commit `2da484c` — first fully-green CI run across all jobs.

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
