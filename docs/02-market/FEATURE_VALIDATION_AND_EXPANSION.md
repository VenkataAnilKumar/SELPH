# SELPH Feature Validation and Expansion Plan

Date: April 27, 2026
Status: Working product strategy document

## Goal

Validate whether current SELPH features solve high-value user pain for the MVP segment, then prioritize new features that increase approval rate, retention, and paid conversion.

## Validation Framework

Each feature is scored on a 1 to 5 scale across five dimensions:

1. User pain severity
2. Differentiation versus alternatives
3. Feasibility within current architecture
4. Safety and compliance risk
5. Revenue impact

Priority formula:
Priority score = (Pain + Differentiation + Feasibility + Revenue) - Risk

## Current Feature Validation

| Feature | Pain | Diff | Feasibility | Revenue | Risk | Priority Score | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| Identity profile and style learning | 5 | 5 | 4 | 5 | 2 | 17 | Core moat, must ship |
| Text draft generation in user voice | 5 | 4 | 4 | 5 | 2 | 16 | Core MVP feature |
| Human approval loop | 5 | 4 | 5 | 4 | 1 | 17 | Trust engine, must ship |
| Confidence scoring and routing | 4 | 4 | 4 | 4 | 2 | 14 | Strong quality lever |
| Transparent and private modes | 4 | 5 | 4 | 4 | 2 | 15 | Important trust and branding feature |
| Audit logs and anomaly detection | 4 | 4 | 3 | 4 | 2 | 13 | Essential for scale and compliance |
| Instagram and Gmail channel support | 5 | 3 | 3 | 5 | 3 | 13 | Valuable but operationally complex |
| Voice clone | 3 | 4 | 3 | 4 | 3 | 11 | High wow, not MVP-critical |
| Avatar clone | 2 | 4 | 2 | 3 | 3 | 8 | Defer until text value is proven |

## What This Means

1. Keep MVP focused on text twin quality and approval loop.
2. Treat voice as optional acceleration after text metrics stabilize.
3. Treat avatar as a phase after measurable retention improvement from voice or channel growth.

## Core Product Hypotheses to Validate

1. If draft quality is high, users will keep the product active weekly.
2. If approval action is one tap and fast, creators will route meaningful message volume through SELPH.
3. If trust controls are explicit, users will allow limited autonomy over time.
4. If identity fidelity is strong, users will pay premium tiers.

## Validation Experiments for Current Features

### Experiment A: Draft Quality and Identity Fidelity
- Metric: Twin approval rate without edits
- Success threshold: greater than 80 percent by week 4 of active usage
- Method: 50 to 100 real message samples per pilot user

### Experiment B: Time Saved Value
- Metric: Minutes saved per day and weekly active usage
- Success threshold: at least 30 minutes saved per active user per day
- Method: in-app time tracking from draft received to decision made

### Experiment C: Trust Adoption
- Metric: Percentage of users enabling low-risk autonomy settings
- Success threshold: at least 25 percent of retained users enable one low-risk category by week 8
- Method: staged feature flag with explicit opt-in

### Experiment D: Monetization Signal
- Metric: Conversion from free to paid at 30 days
- Success threshold: at least 8 percent for creator segment pilot
- Method: paywall around interaction limits and advanced channel controls

## New Feature Opportunities

### Tier 1: High Priority Expansion

1. Calibration Studio
- What it is: weekly guided refinement with side-by-side draft comparisons
- Why it matters: directly improves approval rate
- Validation metric: increase in approval rate by at least 10 points over 4 weeks

2. Persona Modes by context
- What it is: channel or audience-specific style presets such as fan mode, sponsor mode, client mode
- Why it matters: reduces edit friction for mixed communication contexts
- Validation metric: edit rate reduction by at least 20 percent in multi-channel users

3. Smart Inbox Prioritization
- What it is: rank incoming messages by business value and urgency
- Why it matters: turns SELPH into decision leverage, not only draft assistance
- Validation metric: response time reduction for high-value threads by at least 40 percent

4. Relationship Memory Cards
- What it is: compact sender profile with interaction history and preferences
- Why it matters: improves reply quality and personalization
- Validation metric: quality score uplift for repeat contacts by at least 15 percent

### Tier 2: Strategic Expansion

5. Offer and Lead Assistant
- What it is: detect collaboration or lead intent and draft monetization-aware responses
- Why it matters: creates direct creator revenue impact
- Validation metric: increase in qualified lead replies and deal conversion

6. Content Repurposing Agent
- What it is: convert high-performing responses into post ideas, newsletter snippets, or scripts
- Why it matters: bridges communication and content output
- Validation metric: weekly output increase and retention impact

7. Team Twin for agencies
- What it is: shared operating model for creator teams with approval tiers
- Why it matters: unlocks higher-ticket plans
- Validation metric: multi-seat activation and team retention at 60 days

### Tier 3: Future Bets

8. Voice-first response mode
- What it is: quick voice draft and send workflow for mobile
- Why it matters: speed and creator authenticity
- Validation metric: voice reply usage share and retention delta

9. Avatar response for premium fan experiences
- What it is: paid personalized short video responses
- Why it matters: premium monetization, not baseline utility
- Validation metric: attach rate and margin per response

10. Twin analytics and coaching
- What it is: dashboard showing trust trends, tone drift, and performance recommendations
- Why it matters: long-term optimization and stickiness
- Validation metric: 30-day retention uplift

---

## Expansion Features — Gap Analysis (April 2026)

The following 10 features were identified as gaps not covered in the original roadmap. Full technical specs are in [SELPH_Feature-Expansion-Spec.md](../03-specs/SELPH_Feature-Expansion-Spec.md).

Priority formula: (Pain + Differentiation + Feasibility + Revenue) - Risk

| Feature | Pain | Diff | Feasibility | Revenue | Risk | Priority Score | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| Batch Pattern Approval | 5 | 5 | 4 | 5 | 1 | 18 | Must-ship for creator segment |
| Twin Briefing / Context Injection | 5 | 4 | 5 | 4 | 1 | 17 | Must-ship before public launch |
| VIP Override / Relationship Tiers | 4 | 4 | 5 | 4 | 1 | 16 | High-value, low-effort control feature |
| Proactive Twin | 4 | 5 | 3 | 5 | 2 | 15 | Retention differentiator, Phase 2 |
| Crisis / Surge Mode | 4 | 4 | 4 | 3 | 1 | 14 | Required before high-volume creator launch |
| Multi-Identity Profiles | 3 | 5 | 3 | 5 | 2 | 14 | Pro tier value unlock |
| Style Evolution / Identity Refresh | 3 | 4 | 4 | 4 | 1 | 14 | Long-term retention driver |
| Twin Verification Public API | 3 | 5 | 3 | 3 | 1 | 13 | Trust infrastructure, ecosystem play |
| On-Device Processing Mode | 3 | 4 | 2 | 4 | 2 | 11 | Enterprise prerequisite, Phase 3 |
| Twin-to-Twin Protocol | 3 | 5 | 2 | 3 | 3 | 10 | Platform moat, requires twin critical mass |

### Key Findings

- **Batch Pattern Approval** is the single most important missing feature for high-volume creators. Without it, the approval loop becomes a bottleneck at scale and defeats the core value proposition.
- **Twin Briefing** is low-effort and high-impact. Without it, the twin sends contextually wrong replies during live events, campaigns, and announcements.
- **VIP Override** is a simple data model change with outsized user trust impact. Users need to know their most important relationships bypass the AI.
- **Crisis / Surge Mode** must be in place before any creator with >100K followers uses the product. A viral event without it is a trust-destroying failure scenario.
- **Twin-to-Twin Protocol** is the long-term platform moat but requires critical twin mass first. Design it now, ship it in Phase 3.

## Recommended Roadmap Order

Phase 1, next 4 to 8 weeks:
1. Calibration Studio
2. Persona Modes
3. Smart Inbox Prioritization
4. Twin Briefing / Context Injection (added — low effort, critical for launch)
5. VIP Override / Relationship Tiers (added — simple, high trust value)
6. Batch Pattern Approval (added — essential for creator segment at volume)

Phase 2, following 8 to 16 weeks:
1. Relationship Memory Cards
2. Offer and Lead Assistant
3. Content Repurposing Agent
4. Crisis / Surge Mode (added — needed before public launch)
5. Proactive Twin (added — differentiation and retention layer)
6. Multi-Identity Profiles (added — Pro tier value)
7. Style Evolution / Identity Refresh (added — long-term retention)
8. Twin Verification Public API (added — trust infrastructure)

Phase 3:
1. Team Twin
2. Voice-first response mode
3. Avatar response as premium feature
4. On-Device Processing Mode (added — enterprise prerequisite)
5. Twin-to-Twin Protocol (added — platform moat feature)

## MVP Guardrails

1. Do not add avatar work until text twin approval and retention metrics are healthy.
2. Do not broaden channel count until Instagram and Gmail reliability meet targets.
3. Keep safety constraints constant while testing new autonomy features.
4. Use feature flags and staged rollouts for every new capability.

## Decision Dashboard Metrics

Track weekly:

1. Twin approval rate without edits
2. Edit rate and reject rate
3. Time to decision per draft
4. Weekly active users and day-30 retention
5. Free to paid conversion
6. Messages processed per active user
7. Moderation block rate and false-positive rate
8. Autonomy opt-in rate by stage

## Immediate Next Actions

1. Add this scoring model to product review cadence.
2. Run Experiments A and B with first pilot cohort.
3. Build Calibration Studio as first expansion feature.
4. Re-score all features every two weeks using real usage data.
