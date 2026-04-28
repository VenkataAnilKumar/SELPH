# Release Readiness Checklist

Date: 2026-04-28
Target Release: 0.7.1
Branch for release candidate work: feature/phase7-planning

## 1) Code and Branch State

- [ ] main branch is clean and synced with origin/main
- [ ] release candidate branch rebased onto latest main
- [ ] no unreviewed direct commits on main

## 2) Backend Validation

- [x] full backend tests pass
- [x] channel integration tests pass
- [x] no warning regression in backend test runs

## 3) Security Validation

- [x] signed OAuth state validation for channel callbacks
- [x] production JWT secret enforcement guard active
- [x] production auth rate limit configured
- [x] optional Gmail webhook shared-secret check available

## 4) Performance Validation

- [x] Instagram webhook path avoids repeated page-to-user lookups per request
- [ ] p95 API latency report captured from staging
- [ ] queue throughput snapshot captured from worker metrics

## 5) Configuration and Secrets

- [ ] JWT_SECRET_KEY set to strong 32+ character value in production
- [ ] GOOGLE_WEBHOOK_SECRET set if Gmail webhook secret protection is required
- [ ] AUTH_RATE_LIMIT_PER_MINUTE tuned for expected traffic profile
- [ ] ENFORCE_PRODUCTION_JWT_SECRET=true in production env

## 6) Release Tag and Notes

Recommended tag after merge to main:
- v0.7.1

Commands:
- git checkout main
- git pull --ff-only origin main
- git tag -a v0.7.1 -m "Release 0.7.1: Voice phase complete, security/perf hardening"
- git push origin v0.7.1

## 7) Deployment Gate

- [ ] migration plan confirmed (if any DB changes included)
- [ ] rollback plan documented
- [ ] smoke tests pass post-deploy
- [ ] monitoring and alerts verified for first 60 minutes
