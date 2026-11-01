# SELPH — Security Acceptance Criteria

Each control lists what must be true, how it is enforced in code, and the test that proves it.
Run all of them with `cd src/backend && pytest tests/test_token_revocation.py tests/test_security_hardening.py tests/test_moderation_rules.py tests/test_golden_evals.py`.

| # | Control | Acceptance criterion | Enforced in | Proven by |
|---|---|---|---|---|
| S1 | Server-side logout | After `POST /v1/auth/logout` the access token is rejected immediately; other sessions keep working | `middleware/auth.py`, `services/token_revocation.py`, table `revoked_tokens` | `test_logout_revokes_access_token_immediately`, `test_logout_is_idempotent_for_other_sessions` |
| S2 | Token typing | Refresh tokens and purpose-scoped tokens (OAuth `state`, which travels through Meta/Google redirects) can never act as an API bearer token | `security.verify_access_token` | `test_refresh_token_cannot_be_used_as_bearer`, `test_oauth_state_token_cannot_be_used_as_bearer` |
| S3 | Refresh rotation | A refresh token is single-use; replaying it fails; logout can revoke it | `routers/auth.py` | `test_refresh_with_refresh_token_rotates_and_revokes_old` |
| S4 | Credentials encrypted at rest | Channel OAuth tokens are stored as `enc:v1:<fernet>`; plaintext never reaches the database | `crypto.py`, `EncryptedString` column type | `test_database_row_holds_ciphertext_but_orm_returns_plaintext` |
| S5 | Key management | Production refuses to store credentials without `CREDENTIAL_ENCRYPTION_KEY`; keys rotate with zero downtime; legacy plaintext rows still read and can be migrated | `crypto.py`, `scripts/encrypt_credentials.py`, `/ready` | `test_production_requires_explicit_key`, `test_key_rotation_*`, `test_legacy_plaintext_*` |
| S6 | Webhooks fail closed | Instagram and Gmail webhooks return 503 when their signing secret is unset; unsigned mode exists only for development, behind an explicit flag, and is ignored in production | `routers/channels.py::_reject_unsigned_webhook` | `test_*_webhook_rejected_when_secret_unset`, `test_unsigned_webhooks_allowed_only_in_development_with_opt_in` |
| S7 | Webhook authenticity | Instagram `X-Hub-Signature-256` is HMAC-verified in constant time and never against an empty key; Gmail shared secret accepted via header or `?token=` (Pub/Sub push cannot set headers); non-ASCII input is rejected, not a 500 | `channels/instagram.py`, `routers/channels.py` | `test_instagram_signature_validation`, `test_empty_app_secret_never_validates_a_signature`, `test_gmail_*` |
| S8 | Inbound content is untrusted | Prompt-injection attempts and sensitive requests (self-harm, medical, legal, financial) are flagged for the human and never auto-answered | `services/moderation.py` | `test_moderation_rules.py`, golden cases `i01–i06`, `s01–s06` |
| S9 | Drafts never invent commitments | Replies contain no invented numbers, prices, links, or promises | `services/fallback_drafter.py` | `test_golden_evals.py` (gate: >= 95%, currently 100%) |
| S10 | Approval is mandatory | No endpoint sends a reply without a user decision on the draft | `routers/drafts.py`, `routers/channels.py::send-reply` | `test_acceptance.py`, `test_endpoints.py` |
| S11 | Readiness reflects security posture | `/ready` reports insecure JWT secret, missing encryption key, and missing webhook secrets | `routers/health.py` | `test_readiness_reports_missing_key_in_production` |
| S12 | Metrics not publicly exposed | `/metrics` is token-protected, and hidden in production without a token | `routers/health.py` | `test_metrics_token_protects_endpoint`, `test_metrics_hidden_in_production_*` |

## Production checklist

- [ ] `JWT_SECRET_KEY` is 32+ random characters (`/ready` -> `jwt_secret.ok`)
- [ ] `CREDENTIAL_ENCRYPTION_KEY` set; `python scripts/encrypt_credentials.py --apply` run once on existing data
- [ ] `META_APP_SECRET` and `GOOGLE_WEBHOOK_SECRET` set; Pub/Sub push URL ends with `?token=<secret>`
- [ ] `ALLOW_UNSIGNED_WEBHOOKS` is `false` (ignored in production anyway)
- [ ] `METRICS_TOKEN` set and configured in the Prometheus scrape job
- [ ] `/ready` returns `ok=true` for every check

## Known gaps (not covered here)

- Access tokens still live 24 h by default; revocation closes the logout gap, but a shorter TTL with refresh would reduce exposure further.
- The per-process auth rate limiter is in-memory; a multi-replica deployment needs a shared (Redis) limiter.
- Deletion certificates for the privacy workflow are specified in `SELPH_Privacy-Consent.md` but not yet implemented.
