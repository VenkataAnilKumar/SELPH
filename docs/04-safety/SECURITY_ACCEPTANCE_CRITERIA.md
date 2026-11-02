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
| S13 | Twin signing secrets encrypted at rest | The HMAC secret behind each twin's signed replies is stored as `enc:v1:...`; legacy plaintext still signs and is migrated by `scripts/encrypt_credentials.py` | `models/twin_certificate.py`, `crypto.py` | `test_twin_signing_secret_is_encrypted_in_the_database`, `test_legacy_plaintext_twin_secret_still_signs` |
| S14 | Auth throttling holds across replicas | Login, signup and refresh are limited per client in Redis, degrade to an in-process counter if Redis is down, and never grow memory without bound | `ratelimit.py` | `test_auth_hardening.py` |
| S15 | Token lifetimes are configurable | `JWT_EXPIRATION_HOURS` and `JWT_REFRESH_EXPIRATION_DAYS` actually control token lifetime | `services/auth.py` | `test_token_lifetimes_come_from_settings` |
| S16 | Delivery happens once, only when approved | Approve/edit queues delivery only for clean drafts on connected channels; a draft cannot be decided twice (atomic claim); the service refuses unapproved drafts; transient channel failures retry | `services/draft.py`, `services/channel.py`, `tasks/send_reply.py` | `test_delivery_on_approve.py`, `test_service_refuses_to_send_unapproved_drafts` |
| S17 | Right to erasure | `DELETE /v1/privacy/account` (password + exact confirmation phrase) removes every row of the user in one transaction, keeps audit logs anonymized, and returns a signed, publicly verifiable deletion certificate | `services/erasure.py`, `routers/privacy.py` | `test_erasure.py` (also verified against Postgres with enforced foreign keys) |
| S18 | Right to portability | `GET /v1/privacy/export` returns the user's data as JSON with secrets excluded and never includes other users' data | `services/erasure.py` | `test_export_contains_own_data_and_no_secrets` |
| S12 | Metrics not publicly exposed | `/metrics` is token-protected, and hidden in production without a token | `routers/health.py` | `test_metrics_token_protects_endpoint`, `test_metrics_hidden_in_production_*` |

## Production checklist

- [ ] `JWT_SECRET_KEY` is 32+ random characters (`/ready` -> `jwt_secret.ok`)
- [ ] `CREDENTIAL_ENCRYPTION_KEY` set; `python scripts/encrypt_credentials.py --apply` run once on existing data
- [ ] `META_APP_SECRET` and `GOOGLE_WEBHOOK_SECRET` set; Pub/Sub push URL ends with `?token=<secret>`
- [ ] `ALLOW_UNSIGNED_WEBHOOKS` is `false` (ignored in production anyway)
- [ ] `METRICS_TOKEN` set and configured in the Prometheus scrape job
- [ ] `/ready` returns `ok=true` for every check
- [ ] `python scripts/encrypt_credentials.py --apply` run after enabling the encryption key (covers channel tokens and twin signing secrets)
- [ ] `JWT_EXPIRATION_HOURS` set deliberately (shorter is safer; clients can refresh with the refresh token)
- [ ] Run behind a proxy? Start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy ip>` so the rate limiter sees real client IPs

## Known gaps (not covered here)

- Voice/avatar models held by third-party providers are not deleted on account erasure: the provider integration has no deletion API. The deletion certificate says so; request deletion from the provider directly.
- No confirmation email is sent after erasure (SELPH has no outbound email service); the certificate is the confirmation.
- Erasing an account also deletes twin-to-twin sessions it took part in, including the counterparty's copy of that session.
- Deletion certificates are signed with `CERTIFICATE_SIGNING_KEY` (or the JWT secret); rotating the key stops old certificates from verifying.
