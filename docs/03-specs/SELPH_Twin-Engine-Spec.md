# SELPH — Twin Engine Specification

> Version: 1.0
> Created: 2026-04-24
> Folder: 03-specs
> Status: Draft — Required before Phase 2 build

---

## Overview

The Twin Engine is the AI core of SELPH. It takes an incoming message, loads the user's identity model, generates a draft response that sounds like the user, scores how confident it is, and routes the draft to the human approval loop.

This document specifies the exact prompt architecture, confidence scoring formula, draft generation pipeline, and learning mechanism.

---

## Twin Engine Pipeline

```
Incoming Message (via Celery task: process_incoming_message)
      ↓
[1] Context Loader      → Fetches identity profile + conversation history
      ↓
[2] Apply Briefings     → Injects active twin briefings as high-priority context
      ↓
[3] Select Profile      → Picks correct identity profile (multi-identity routing)
      ↓
[4] Check VIP Tier      → VIP senders bypass twin → direct notify; others continue
      ↓
[5] Channel Router      → Applies channel-specific style constraints
      ↓
[6] Prompt Builder      → Constructs system + user prompt dynamically
      ↓
[7] Draft Generator     → Claude API call via LLM Proxy → structured JSON response
      ↓
[8] Confidence Scorer   → Computes 0.0–1.0 confidence score
      ↓
[9] Content Moderator   → Safety check before routing to human
      ↓
[10] Check T2T          → T2T handshake? Route to negotiation sub-graph
      ↓
[11] Approval Router    → WebSocket push (active) or FCM push (offline) with draft
      ↓
[12] Feedback Processor → Updates identity model; logs to audit_logs
```

For the full LangGraph node wiring with conditional edges, see [SELPH_System-Architecture.md](../05-technical/SELPH_System-Architecture.md#2-twin-engine-langgraph-stategraph).

---

## Step 1 — Context Loader

```python
@dataclass
class TwinContext:
    identity_profile: IdentityProfile
    channel_profile: ChannelProfile
    conversation_history: list[Message]   # last 5 messages with this sender
    sender_context: SenderContext         # who is messaging
    similar_past_responses: list[str]     # top 3 similar past responses from pgvector
    incoming_message: str
    channel: str

def load_context(user_id: str, incoming_message: str, sender_id: str, channel: str) -> TwinContext:
    profile = get_identity_profile(user_id)
    channel_profile = get_channel_profile(user_id, channel)
    history = get_conversation_history(user_id, sender_id, channel, limit=5)
    sender = get_sender_context(sender_id, channel)

    # Retrieve semantically similar past responses using pgvector (co-located with identity data)
    # pgvector on Railway PostgreSQL — all vector search co-located, avoids network hop, <5ms
    query_vector = embed(incoming_message)
    similar_responses = db.query("""
        SELECT content FROM identity_samples
        WHERE profile_id = :profile_id
        ORDER BY embedding <=> :query_vector
        LIMIT 3
    """, profile_id=profile.id, query_vector=query_vector)

    return TwinContext(
        identity_profile=profile,
        channel_profile=channel_profile,
        conversation_history=history,
        sender_context=sender,
        similar_past_responses=similar_responses,
        incoming_message=incoming_message,
        channel=channel
    )
```

---

## Step 2 — Channel Router

Each channel applies style constraints on top of the base identity:

```python
CHANNEL_CONSTRAINTS = {
    "instagram_dm": ChannelConstraints(
        style_hint="casual, warm, short",
        max_words=150,
        format="plain text, no markdown",
        emoji_multiplier=1.2,        # slightly more emoji than baseline
        formality_adjustment=-1      # more casual than baseline
    ),
    "gmail": ChannelConstraints(
        style_hint="professional, structured, clear",
        max_words=300,
        format="with greeting and sign-off, light markdown ok",
        emoji_multiplier=0.2,        # almost no emoji
        formality_adjustment=+1      # slightly more formal
    ),
    "twitter_dm": ChannelConstraints(
        style_hint="concise, punchy, direct",
        max_words=100,
        format="plain text",
        emoji_multiplier=1.0,
        formality_adjustment=0
    ),
    "whatsapp": ChannelConstraints(
        style_hint="conversational, warm, voice-note friendly",
        max_words=120,
        format="plain text, casual",
        emoji_multiplier=1.1,
        formality_adjustment=-1
    )
}
```

---

## Step 3 — Prompt Builder

The system prompt is constructed dynamically per user + channel:

### System Prompt Template

```python
def build_system_prompt(ctx: TwinContext) -> str:
    p = ctx.identity_profile
    ch = ctx.channel_profile
    constraints = CHANNEL_CONSTRAINTS[ctx.channel]

    emoji_level = "frequent" if (p.emoji_usage * constraints.emoji_multiplier) > 0.5 else "minimal"
    formality = clamp(p.formality_level + constraints.formality_adjustment, 1, 5)
    formality_label = {1: "very casual", 2: "casual", 3: "neutral", 4: "professional", 5: "formal"}[formality]

    samples_block = format_samples(ctx.similar_past_responses, ctx.channel)

    return f"""You are the digital twin of {p.first_name} {p.last_name}.

## Who You Are
- Domain: {p.domain} ({p.sub_domain or "general"})
- Title: {p.professional_title or p.domain}
- Personality: {", ".join(p.personality_words)}
- Bio: {p.bio_summary or "No bio provided"}

## Your Communication Style
- Tone: {p.tone}
- Formality: {formality_label}
- Average response length: {p.avg_response_length} words (range: {p.response_length_min}–{p.response_length_max})
- Emoji usage: {emoji_level}
- Greeting style: {p.greeting_style or "none"}
- Sign-off style: {p.sign_off_style or "none"}

## Topics
You speak knowledgeably about: {", ".join(p.topics_known[:10]) or "general topics"}
You never discuss: {", ".join(p.topics_avoided) or "nothing specific"}

## Channel Context ({ctx.channel})
Style hint: {constraints.style_hint}
Max length: {constraints.max_words} words
Format: {constraints.format}

## Real Examples of How {p.first_name} Responds on {ctx.channel}
{samples_block}

## Absolute Rules
1. Respond EXACTLY as {p.first_name} would — same voice, same energy
2. Never say you are an AI unless directly and explicitly asked
3. If the topic is in the avoided list → respond: "That's not something I cover — let me get back to you"
4. If you are uncertain about facts → respond: "Let me check on that and get back to you"
5. Never make financial commitments, legal statements, or medical claims
6. Match the emotional energy of the incoming message
7. Stay within {constraints.max_words} words
8. Return ONLY valid JSON — no extra text before or after
"""
```

### User Prompt Template

```python
def build_user_prompt(ctx: TwinContext) -> str:
    history_block = format_history(ctx.conversation_history)
    sender_note = f"(You've spoken with {ctx.sender_context.name} {ctx.sender_context.interaction_count} times before)" \
                  if ctx.sender_context.interaction_count > 0 else "(First interaction with this person)"

    return f"""
## Conversation History
{history_block if history_block else "No prior conversation with this sender."}

## Incoming Message
From: {ctx.sender_context.name} {sender_note}
Platform: {ctx.channel}
Message: "{ctx.incoming_message}"

## Your Task
Draft a response as {ctx.identity_profile.first_name}.

Return this exact JSON:
{{
  "draft": "your response text here",
  "confidence_factors": {{
    "topic_known":       <0.0-1.0>,
    "length_match":      <0.0-1.0>,
    "tone_match":        <0.0-1.0>,
    "no_avoided_topics": <0.0-1.0>,
    "sample_similarity": <0.0-1.0>
  }},
  "reasoning": "one sentence explaining your draft choice",
  "flags": []
}}

If you cannot draft a response (topic avoided, insufficient context), set "draft" to null and explain in "flags".
"""
```

---

## Step 4 — Draft Generator

The Draft Generator uses LiteLLM as the model gateway. Users can choose their preferred LLM and bring their own API key. Default model is claude-sonnet-4-6.

```python
from litellm import acompletion

async def generate_draft(ctx: TwinContext, user_model: str = "claude-sonnet-4-6", user_api_key: str = None) -> DraftResult:
    # LiteLLM routes to correct provider — same interface regardless of model chosen
    response = await acompletion(
        model=user_model,           # user-selectable: claude-sonnet-4-6, gpt-5, gemini/..., ollama/llama3, etc.
        max_tokens=600,
        temperature=0.7,            # some creativity but not too random
        api_key=user_api_key,       # BYOK — None uses SELPH default key
        messages=[
            {"role": "system", "content": build_system_prompt(ctx)},
            *format_history_for_api(ctx.conversation_history),
            {"role": "user", "content": build_user_prompt(ctx)}
        ]
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Retry once with stricter JSON instruction
        result = await retry_with_json_fix(ctx, raw, user_model, user_api_key)

    return DraftResult(
        draft=result["draft"],
        confidence_factors=result["confidence_factors"],
        reasoning=result["reasoning"],
        flags=result.get("flags", []),
        model_used=user_model,
        tokens_used=response.usage.prompt_tokens + response.usage.completion_tokens
    )

# Supported models (user-selectable via settings):
SUPPORTED_MODELS = {
    "claude-sonnet-4-6":       "Anthropic — default, best reasoning",
    "claude-opus-4-6":         "Anthropic — most capable",
    "gpt-5":                   "OpenAI — BYOK required",
    "gemini/gemini-2.0-flash": "Google — fast, cost-effective",
    "deepseek/deepseek-chat":  "DeepSeek — budget option",
    "ollama/llama3":           "Local via Ollama — zero API cost",
    "mistral/mistral-large":   "Mistral — EU-hosted option",
}
```

---

## Step 5 — Confidence Scorer

Confidence is computed from 5 weighted factors:

```python
CONFIDENCE_WEIGHTS = {
    "topic_known":       0.25,   # Does the twin know this topic?
    "length_match":      0.15,   # Is response length appropriate?
    "tone_match":        0.25,   # Does tone match identity profile?
    "no_avoided_topics": 0.20,   # Are avoided topics respected?
    "sample_similarity": 0.15    # How similar to past approved responses?
}

def compute_confidence(factors: dict[str, float]) -> float:
    score = sum(factors[k] * CONFIDENCE_WEIGHTS[k] for k in CONFIDENCE_WEIGHTS)
    return round(score, 3)

# Routing thresholds
CONFIDENCE_HIGH   = 0.85    # "Ready to send" — green in app
CONFIDENCE_MEDIUM = 0.65    # "Review suggested" — yellow in app
# Below CONFIDENCE_MEDIUM → "needs_input" — red in app, must edit before sending

def get_confidence_label(score: float) -> str:
    if score >= CONFIDENCE_HIGH:   return "ready"
    if score >= CONFIDENCE_MEDIUM: return "review"
    return "needs_input"
```

### Factor Computation

```python
def compute_confidence_factors(
    draft: str,
    incoming: str,
    profile: IdentityProfile,
    ctx: TwinContext
) -> dict[str, float]:

    # 1. topic_known — is the draft topic in known topics list?
    topic_known = 1.0 if any(t in draft.lower() for t in profile.topics_known) else 0.4
    if any(t in draft.lower() for t in profile.topics_avoided):
        topic_known = 0.0   # hard penalty

    # 2. length_match — is draft within acceptable range?
    word_count = len(draft.split())
    if profile.response_length_min <= word_count <= profile.response_length_max:
        length_match = 1.0
    else:
        deviation = min(
            abs(word_count - profile.response_length_min),
            abs(word_count - profile.response_length_max)
        )
        length_match = max(0.0, 1.0 - (deviation / profile.avg_response_length))

    # 3. tone_match — cosine similarity between draft embedding and style vector
    draft_vector = embed(draft)
    style_vector = db.query("SELECT embedding FROM identity_samples WHERE profile_id = :pid ORDER BY quality_score DESC LIMIT 1", pid=profile.id)[0].embedding
    tone_match = cosine_similarity(draft_vector, style_vector)

    # 4. no_avoided_topics — binary check
    no_avoided = 0.0 if any(t in draft.lower() for t in profile.topics_avoided) else 1.0

    # 5. sample_similarity — similarity to top past responses
    sample_similarities = [
        cosine_similarity(embed(draft), embed(s))
        for s in ctx.similar_past_responses
    ]
    sample_similarity = max(sample_similarities) if sample_similarities else 0.5

    return {
        "topic_known":       round(topic_known, 3),
        "length_match":      round(length_match, 3),
        "tone_match":        round(tone_match, 3),
        "no_avoided_topics": round(no_avoided, 3),
        "sample_similarity": round(sample_similarity, 3)
    }
```

---

## Step 6 — Content Moderator

```python
async def moderate_draft(draft: str, user_id: str) -> ModerationResult:
    checks = {
        "harmful_content":   await check_harmful(draft),
        "financial_advice":  check_financial(draft),
        "legal_advice":      check_legal(draft),
        "medical_advice":    check_medical(draft),
        "pii_exposure":      check_pii(draft),          # phone, email, address in draft
        "impersonation":     check_impersonation(draft) # claiming to be human when asked
    }

    passed = all(checks.values())
    flags = [k for k, v in checks.items() if not v]

    return ModerationResult(passed=passed, flags=flags)
```

---

## Step 7 — Approval Router

```python
def route_to_approval(
    draft: DraftResult,
    confidence: float,
    label: str,
    ctx: TwinContext,
    user_id: str
) -> ApprovalRequest:

    # Store draft pending approval
    draft_id = store_draft(
        user_id=user_id,
        content=draft.draft,
        confidence=confidence,
        confidence_label=label,
        incoming_message=ctx.incoming_message,
        sender=ctx.sender_context,
        channel=ctx.channel,
        expires_at=now() + timedelta(hours=24)
    )

    # Push notification payload
    notification = PushNotification(
        user_id=user_id,
        title=f"{ctx.sender_context.name} messaged you on {ctx.channel}",
        body="Your twin drafted a reply — tap to review",
        data={
            "draft_id": draft_id,
            "confidence": confidence,
            "confidence_label": label,
            "preview": draft.draft[:100]
        }
    )

    firebase.send(notification)

    return ApprovalRequest(draft_id=draft_id, notification_sent=True)
```

---

## Step 8 — Feedback Processor

```python
def process_human_decision(
    draft_id: str,
    action: str,             # "approve" | "edit" | "reject" | "skip"
    edited_content: str | None = None,
    rejection_reason: str | None = None
):
    draft = get_draft(draft_id)

    if action == "approve":
        send_message(draft.content, draft.channel, draft.sender)
        log_audit(draft_id, action="approve", final_content=draft.content)
        update_identity_from_feedback(draft.user_id, draft.content, "approved", draft.channel)

    elif action == "edit":
        send_message(edited_content, draft.channel, draft.sender)
        log_audit(draft_id, action="edit", final_content=edited_content, edit_diff=diff(draft.content, edited_content))
        update_identity_from_feedback(draft.user_id, edited_content, "edited", draft.channel,
                                      edited_version=edited_content)

    elif action == "reject":
        log_audit(draft_id, action="reject", rejection_reason=rejection_reason)
        update_identity_from_feedback(draft.user_id, draft.content, "rejected", draft.channel,
                                      rejection_reason=rejection_reason)

    elif action == "skip":
        log_audit(draft_id, action="skip")
        # No learning signal

    mark_draft_resolved(draft_id, action)
```

---

## Twin Engine Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Draft generation time | < 8 seconds | p95 latency |
| Confidence score accuracy | > 80% match with human rating | Weekly calibration |
| Cold start approval rate | > 60% | First 10 drafts |
| Warm approval rate (50+ drafts) | > 85% | Rolling 20-draft window |
| False moderation block rate | < 2% | % of valid drafts blocked |
| Retry rate (JSON parse failure) | < 5% | % of calls needing retry |

---

## LangGraph State Definition

```python
from typing import TypedDict

class TwinEngineState(TypedDict):
    # Input
    user_id: str
    incoming_message: str
    sender_id: str
    channel: str

    # Computed
    context: dict              # TwinContext serialized
    draft: str | None
    confidence: float
    confidence_label: str      # "ready" | "review" | "needs_input"
    moderation_passed: bool
    moderation_flags: list[str]
    draft_id: str

    # Human decision
    human_action: str | None   # "approve" | "edit" | "reject" | "skip"
    final_content: str | None

    # Audit
    audit_log: list[dict]
    error: str | None
```

---

*Status: Twin Engine Specification v1.0 — Ready for Phase 2 implementation*
