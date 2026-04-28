# SELPH Canonical Policy Matrix

Version: 1.0  
Date: April 27, 2026  
Status: Canonical Source of Truth

## Purpose

This document resolves policy mismatches across SELPH documentation and defines the final enforceable values for:
- Human oversight and autonomy
- Retention and deletion
- Compliance controls
- Incident and takedown SLAs
- Security control minimums

All other SELPH documents must align with this matrix. If a conflict exists, this document takes precedence.

## Document Precedence

Precedence order for policy decisions:

1. This file: SELPH_Canonical-Policy-Matrix.md
2. Privacy and consent architecture
3. Risk mitigation strategy
4. PRD and implementation plans
5. Technical specs and references

## Human Oversight and Autonomy Policy

| Policy Area | Canonical Rule | Applies To |
|---|---|---|
| Outbound user-facing messages | Human approval required in Stage 1 and Stage 2 | All channels |
| Limited autonomy in Stage 2 | Allowed only for pre-approved low-risk categories and only with user opt-in | FAQ-like and low-stakes interactions |
| Stage 3 autonomy | Allowed only for explicitly user-approved categories with immediate rollback and auditability | Selected categories only |
| High-risk categories | Always blocked from autonomous execution | Financial, legal, medical, political, minors |
| Emergency control | One-tap pause must override all queue activity immediately | All users |

### Stage Definitions (Canonical)

| Stage | Behavior | Advancement Requirements |
|---|---|---|
| Stage 1 | Full human approval for all outbound actions | Default at activation |
| Stage 2 | Human approval remains default; optional autonomy for low-risk categories only | At least 50 drafts, approval rate at least 0.85, at least 14 days active |
| Stage 3 | User-defined category autonomy with continuous monitoring | At least 200 drafts, approval rate at least 0.90, at least 28 days in Stage 2, explicit user enablement |

### Downgrade Rules

Automatic downgrade to Stage 1 when any of the following occur:
- Approval rate below 0.60 for at least 20 consecutive drafts
- Security anomaly with confidence above threshold
- User manual downgrade

## Retention and Deletion Policy

| Data Type | Retention | Deletion Trigger | Notes |
|---|---|---|---|
| Government ID artifacts | Immediate post-verification purge | Verification complete | Keep only verification result metadata |
| Face match result | 30 days | Time-based auto-delete | Required for dispute window |
| Raw voice recordings | Maximum 90 days | User request or auto-delete | May be shorter by region |
| Raw avatar recordings | Maximum 90 days | User request or auto-delete | May be shorter by region |
| Voice and avatar model handles | Until account deletion or explicit revoke | User deletion or revoke | Third-party deletion confirmation required |
| Ingested channel content | Until consent revocation or account deletion | Revoke consent or delete account | Per-channel data purge required |
| Identity profile and topics | Until account deletion | Delete account | Included in portability export |
| Draft and interaction logs | 2 years default | Time-based retention or legal hold | Anonymize where required |
| Audit logs | 2 years minimum | Time-based retention policy | Required for compliance and abuse investigation |
| Usage analytics | 90 days identified, then anonymized up to 1 year | Time-based transform | No personal re-identification after anonymization |

### Account Deletion SLA

- User-visible target: complete deletion within 24 hours
- Legal hard maximum: 30 days where jurisdiction requires processing windows
- Deletion certificate: mandatory after completion

## Compliance Control Matrix

| Requirement | Canonical Control | Enforcement Point |
|---|---|---|
| AI interaction transparency | Transparent mode available and default for new users unless private mode explicitly selected | Onboarding and per-conversation settings |
| AI-generated content traceability | Watermarking on text, audio, and video outputs | Output pipeline before send |
| Consent granularity | Separate opt-in per data category and per channel ingestion | Consent service and API guards |
| Consent revocation | Immediate processing stop plus asynchronous data purge workflow | Consent revocation handler |
| Human oversight | Mandatory for non-approved autonomous categories | Draft router and decision service |
| Abuse response | Intake endpoint with severity-based SLA | Trust and safety workflow |

## Incident and Takedown SLA Policy

| Incident Type | Initial Action | SLA |
|---|---|---|
| Critical abuse or harmful AI content | Immediate auto-suspend pending review | 3 hours to takedown action |
| High severity impersonation or fraud | Suspend outbound operations and investigate | 3 hours to containment |
| Medium severity abuse report | Queue for trust and safety review | 24 hours |
| Low severity policy complaint | Standard review path | 72 hours |

## Security Baseline Policy

Minimum required controls before external beta:

1. JWT access token short TTL and refresh token revocation support.
2. Application-level encryption for third-party OAuth tokens and biometric model identifiers.
3. HMAC signature verification on all inbound webhooks.
4. Application-level key management and rotation policy (libsodium, keys stored in Railway environment variables).
5. Immutable audit trail for user and system actions.
6. Deletion workflow with third-party deletion confirmation logging.
7. Rate limiting and abuse throttling on auth, drafts, and report endpoints.

## Observability and Governance Policy

Required dashboards and alerts:

1. Draft generation latency: p50, p95, p99 (SLA: p95 < 10s)
2. Approval funnel: approve, edit, reject, skip rates (north star: approval rate > 80%)
3. Moderation outcomes: pass, block, false-positive review rate
4. Queue health: depth, lag, retry count (Celery queue depth and worker lag)
5. Incident response: open reports by severity and SLA breach count
6. Identity drift score: per-user style divergence (alert if rising >0.20 for cohort)
7. LLM cost per draft: input + output tokens (alert on regression)
8. Surge event frequency: count of crisis/surge activations per day
9. Batch approval rate: % of batch templates approved vs rejected
10. Proactive suggestion acceptance rate: target >35%
11. VIP bypass rate: % of messages going direct to user via VIP tier
12. Twin verification API call volume: external trust signal

Full observability implementation: [SELPH_System-Architecture.md](../05-technical/SELPH_System-Architecture.md)

Governance cadence:

- Weekly policy compliance review
- Monthly retention and deletion audit sampling
- Quarterly policy revision approval

## New Feature Policy Rules (Added 2026-04-27)

| Feature | Policy Rule |
|---|---|
| **Twin Briefing** | Briefing content is moderated before activation. Boundary-type briefings cannot be overridden by high-confidence autonomous sends. Maximum 10 active briefings per user. |
| **VIP Override** | Tier 0 (VIP) and Tier 1 (Priority) senders are permanently exempt from autonomous sending at all trust stages. This cannot be overridden by user autonomy settings. |
| **Batch Pattern Approval** | Batch template content passes full moderation before activation. User must approve each template — no auto-batch-approve regardless of trust stage. Maximum batch size configurable per user. |
| **Crisis / Surge Mode** | Autonomous sends are suspended during active crisis mode regardless of trust stage. No twin action may execute during hard crisis mode without explicit per-message user approval. |
| **On-Device Processing** | On-device mode drafts always route to mandatory human review — confidence scoring is unavailable and autonomous sending is blocked in on-device mode. |
| **Twin-to-Twin Protocol** | T2T negotiation outcomes are always drafts. Neither twin may commit to any agreement without both human owners explicitly approving. T2T is opt-in per session and per user. |
| **Proactive Twin** | Proactive outreach always requires explicit user approval. Twin may not initiate contact autonomously regardless of trust stage. |

## Implementation Notes

All implementation-facing documents should reference this file in their policy section and remove conflicting values.

Document references:
- System Architecture: [SELPH_System-Architecture.md](../05-technical/SELPH_System-Architecture.md)
- Feature Specs: [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md)
- Privacy & Consent: [SELPH_Privacy-Consent.md](./SELPH_Privacy-Consent.md)
- PRD: [PRD.md](../01-product/PRD.md)

Status: All documents aligned with this policy matrix as of 2026-04-27.

## Change Log

- v1.0: Initial canonical consolidation from product, safety, technical, and implementation docs.
