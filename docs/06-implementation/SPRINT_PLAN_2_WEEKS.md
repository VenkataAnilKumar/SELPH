# SELPH Two-Week Execution Sprint Plan

Date: April 27, 2026
Sprint Length: 10 working days
Objective: Reach Demo Ready for text-only twin workflow.

## Sprint Outcome

By Day 10:

1. User can sign up and create identity profile.
2. Incoming message can produce a draft within target latency.
3. User can approve, edit, reject, or skip draft.
4. Decision creates audit trail and updates learning counters.
5. Safety baseline moderates drafts before review.

## Scope Constraints

In scope:
- Text-only twin
- Core auth, profile, draft, and approval flow
- Safety baseline and observability baseline

Out of scope:
- Voice clone
- Avatar clone
- Real Instagram and Gmail production integration
- Advanced autonomy

## Day-by-Day Plan

### Day 1: Architecture freeze and backlog lock
Owners: Tech Lead, Backend, AI, Mobile, DevOps
Outputs:
- Sprint backlog finalized
- Endpoint and schema mapping complete
- Risk register version 1
Acceptance:
- No unresolved architecture blockers for in-scope work

### Day 2: Authentication foundation
Owner: Backend
Outputs:
- Register, login, refresh, logout
- JWT middleware and auth guard
- Standard error contract
Acceptance:
- Auth integration tests pass

### Day 3: Core schema and migrations
Owner: Backend
Outputs:
- Users, tokens, profile, topics, drafts, audit, consents tables
- Migration up and down scripts
Acceptance:
- Fresh database bootstraps cleanly and rollback works

### Day 4: Identity onboarding endpoints
Owners: Backend, AI
Outputs:
- Create, read, patch profile
- Topics create and delete
- Confidence endpoint stub
Acceptance:
- Profile version increments and data integrity checks pass

### Day 5: Twin generation pipeline version 1
Owner: AI
Outputs:
- Context loader
- Prompt builder
- Draft JSON contract
- Parse-retry behavior
Acceptance:
- 20 golden prompts return valid structured output

### Day 6: Approval loop APIs
Owner: Backend
Outputs:
- Pending drafts list
- Draft detail endpoint
- Approve, edit, reject, skip actions
Acceptance:
- Draft lifecycle transitions pass state-machine tests

### Day 7: Client review surface and notifications
Owner: Mobile
Outputs:
- Draft review screen
- Decision actions from UI
- Notification plumbing for draft ready event
Acceptance:
- End-to-end action from notification to decision works

### Day 8: Safety baseline
Owners: AI, Backend
Outputs:
- Moderation gate
- Moderation flags storage
- Anomaly detector hook stubs
Acceptance:
- Failed moderation drafts never enter ready state

### Day 9: Auditability and learning counters
Owners: Backend, AI
Outputs:
- Immutable audit entries for all actions
- Approved, edited, rejected counters update
Acceptance:
- Counter values reconcile with action history

### Day 10: Hardening and demo rehearsal
Owners: All
Outputs:
- Demo runbook
- p95 latency report
- Known issues list and Sprint 2 backlog
Acceptance:
- Demo passes three consecutive runs
- p95 draft latency under 10 seconds in staging-like setup

## Definitions of Done

Functional:
- End-to-end text flow operational with one channel simulator.

Quality:
- Integration tests for critical endpoints and transitions.

Safety:
- Moderation must run before draft review.

Observability:
- Dashboard includes draft latency, approval rate, moderation block rate, and API error rate.

Product:
- Creator persona demo script validated by team.

## Key Risks and Mitigations

1. Prompt instability
- Mitigation: strict JSON schema, retry policy, golden prompt set.

2. State transition defects
- Mitigation: explicit status machine tests and idempotency checks.

3. Scope creep
- Mitigation: enforce text-only scope gate.

4. Latency regression
- Mitigation: measure by Day 8 and optimize context size early.

## Sprint 2 Preview

Expected next priorities:
- Twin Briefing endpoints and injection into twin prompt pipeline
- VIP Override / Sender Tier management endpoints and routing logic
- Batch Pattern Approval — message clustering, template approval, personalized send
- Real Instagram and Gmail channel integration
- Consent revocation automation
- Railway production environment setup (required before channels go live)
- Compliance runbooks and incident playbooks
- Production hardening and cost controls

Sprint 2 implements the three Phase 1 expansion features (Twin Briefing, VIP Override, Batch Pattern Approval) alongside channel integration. Specs: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md)
