# Changelog

All notable changes to this project are documented in this file.

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
