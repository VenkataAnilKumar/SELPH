# SELPH — Risk Mitigation Strategy

> Created: 2026-04-24

Policy precedence and final enforceable values are defined in:
- [SELPH_Canonical-Policy-Matrix.md](./SELPH_Canonical-Policy-Matrix.md)

---

## Master Framework: SELPH SAFE

```
S — Signed Consent     → legal protection at signup
A — Audit Trail        → every action logged
F — Filtered Output    → content moderation on all outputs
E — Escalate to Human  → low confidence = human takes over
```

---

## 1. Legal & Regulatory Risk

**Risks:** EU AI Act, India IT Rules 2026, US Take It Down Act, deepfake impersonation liability

### Solutions

### Transparent Mode = Default
- Every twin interaction labeled "Powered by SELPH"
- Automatically EU AI Act compliant from day 1
- No retroactive labeling work needed

### Consent-First Architecture
- User records explicit video consent at signup
- "I [name] authorize SELPH to create my digital twin"
- Stored as legal proof — protects company and user
- Cannot create someone else's twin — only your own

### Watermarking All Outputs
- Every twin-generated message, video, and audio carries an invisible digital watermark
- Traceable back to the account if misused
- Protects against fraud liability

### Content Moderation Layer
- Twin cannot send anything that violates platform policies
- Harmful or illegal content blocked before reaching user
- Meets India's 3-hour takedown requirement
- Automated + human review escalation path

### Jurisdiction-Aware Compliance
- Detect user's country → apply correct legal rules automatically
- EU users → AI Act rules enforced
- India users → IT Rules 2026 enforced
- US users → state-level rules applied

---

## 2. Technical Risk

**Risks:** Identity drift, latency, data privacy, hallucination

### Solutions

### Identity Drift Prevention
- Weekly "identity calibration" — twin shows 5 sample responses
- User rates each 1–5 stars
- Low scores trigger retraining on recent data
- Twin stays aligned with who the user is today, not who they were at signup

### Latency
- Default to open-source: Chatterbox (voice, MIT) + Linly-Talker (avatar, MIT) — self-hostable, zero API cost
- Optional premium: ElevenLabs (voice) + HeyGen (avatar) for users who prefer managed cloud quality
- LiteLLM eliminates LLM vendor lock-in — automatic fallback if one provider is down or rate-limited
- SELPH focuses on identity + agent layer; audio/video generation is pluggable and swappable

### Data Privacy
- All personal data encrypted end-to-end
- Device data processed on-device where possible
- User owns their data — full export and delete at any time
- Zero third-party data selling — core product promise
- SOC 2 Type II audit initiated Month 3, certification targeted by Month 9

### Hallucination Prevention
- Twin never responds outside its knowledge boundary
- Fallback: "I don't have enough context on this — let me check with [Name]"
- Confidence scoring on every response
- Low confidence score → escalate to human immediately
- No fabrication of facts, commitments, or opinions not grounded in user data

---

## 3. Trust Risk

**Risks:** Users don't trust AI with their identity. Recipients don't trust the twin.

### Solutions

### Graduated Trust Model
```
Stage 1 — Draft Mode (default for all users)
Twin drafts everything → user approves every response
User builds familiarity and confidence
→ Advances to Stage 2 after: 50 approved drafts + >85% approval rate over 2 weeks

Stage 2 — Semi-Autonomous Mode
Human approval remains the default for outbound actions
Low-stakes autonomy is optional and requires explicit user opt-in
High-risk categories remain blocked from autonomous execution
→ Advances to Stage 3 after: 200 approved drafts + >90% approval rate over 4 weeks

Stage 3 — Trusted Mode
Twin earns category-limited autonomy in user-defined categories with continuous monitoring
User defines which categories are fully autonomous vs. always-approve
→ Trust score displayed in app — user can downgrade at any time
```

### Full Audit Log
- Every action the twin takes is logged with timestamp
- User reviews complete history in dashboard
- Weekly summary: "Your twin sent 47 messages this week — review here"
- Nothing happens without a trace

### One-Tap Override
- User can pause or stop twin instantly from any screen
- Emergency stop available at all times
- Twin goes fully silent when paused — no queued actions execute

### Recipient Trust (Transparent Mode)
- "You're talking to [Name]'s SELPH — their Digital Twin"
- Verification link to confirm twin is legitimate
- Digital certificate of authenticity issued per twin
- Transparent mode makes trust a feature, not a deception

---

## 4. Ethical Risk

**Risks:** Misuse for fraud, impersonation, harassment, political deepfakes

### Solutions

### Hard Identity Verification at Signup
- Government ID check required
- Face match to ID verified
- Users can only create their own twin — never someone else's
- Makes malicious twin creation structurally impossible

### Usage Boundaries (Default Blocked)
```
BLOCKED by default:
├── Financial transactions
├── Legal documents and contracts
├── Medical advice
├── Political content
└── Content involving minors

UNLOCKED only with explicit user opt-in:
├── Business proposals
├── Client agreements (with review)
└── Public statements
```

### Anomaly Detection
- Twin behavior suddenly changes → auto-pause + alert
- Account accessed from unusual location → security hold
- Unusual spike in message volume → flag for review
- Machine learning model trained on normal twin behavior per user

### Report & Takedown System
- Anyone can report a twin misusing their likeness
- High-severity content (harmful, explicit, political): **3-hour takedown SLA** (India IT Rules 2026 compliant)
- All other reports: 24-hour investigation SLA
- Account suspended immediately during active review
- Dedicated trust and safety team for escalations

---

## 5. Summary Risk Register

| Risk | Severity | Solution | Effort | Status |
|---|---|---|---|---|
| EU AI Act non-compliance | High | Transparent mode default + watermark | Low | Design-time |
| India IT Rules violation | High | Content moderation + takedown flow | Medium | Build-time |
| Deepfake impersonation fraud | High | ID verification at signup | Medium | Build-time |
| Identity drift | Medium | Weekly calibration checks | Low | Build-time |
| High latency | Medium | Chatterbox + Linly-Talker (self-hosted) or ElevenLabs + HeyGen (cloud, optional) | Low | Design-time |
| Data privacy breach | High | On-device processing + E2E encryption | High | Architecture |
| Hallucination / wrong output | Medium | Confidence scoring + human fallback | Medium | Build-time |
| User trust breakdown | Medium | Graduated autonomy + audit logs | Medium | Build-time |
| Misuse for fraud | High | Hard usage boundaries + anomaly detection | Medium | Build-time |
| Unauthorized twin creation | High | Face + ID verification | Medium | Build-time |

---

## 6. Safety Architecture Diagram

```
User Signs Up
     ↓
[ID Verification + Video Consent Recorded]
     ↓
Twin Created
     ↓
Incoming Task/Message
     ↓
[Content Moderation Check]
     ↓
Pass                    Fail
  ↓                       ↓
Twin Drafts Response    Block + Alert User + Log Violation
  ↓
[Confidence Scoring]
  ↓
High Confidence (≥0.85)     Low Confidence (<0.65)     Medium (0.65-0.84)
  ↓                              ↓                           ↓
"Ready to Send"           "Needs Your Input"          "Review Suggested"
  ↓                              ↓                           ↓
  └──────────────────────────────┴───────────────────────────┘
                                 ↓
                    [Watermark Applied to Draft]
                                 ↓
                    Sent to User via Push Notification
                                 ↓
                    User Approves / Edits / Rejects
                                 ↓
                    [Audit Log Entry Created]
                                 ↓
             Approved/Edited → Response Delivered
             Rejected        → No send, reason logged
                                 ↓
                    [Twin Learns from Decision]
```

---

## Conclusion

Every identified risk has a concrete, buildable solution.
None of the risks are blockers — they are design requirements.

The safest path is to treat SELPH SAFE not as a compliance layer
but as a core product feature. Safety = trust. Trust = adoption.

> "The most trusted digital twin is the one that never acts without you knowing."

---

*Status: Risk Mitigation Strategy — Approved for PRD Phase*
