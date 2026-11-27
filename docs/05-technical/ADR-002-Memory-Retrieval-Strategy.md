# ADR-002: Short-Term Memory Retrieval for Twin Context

## Status

Implemented — 2026-11-03 (feature flag default off)
Fully restored with stopword filtering, relative timestamps, and debug logging — 2026-11-07
Richer relative timestamps (yesterday, last week) — 2026-11-08
Configurable candidate pool size — 2026-11-09
Configurable top-K selection — 2026-11-10
Configurable scoring weights (recency / overlap) — 2026-11-11
Optional time-based recency decay (exponential, configurable half-life) — 2026-11-12
Optional minimum hybrid score threshold — 2026-11-13
Structured hybrid_history_selection metric events — 2026-11-14
Optional history prompt character limit with truncation metric — 2026-11-15
Optional diversity threshold to reduce near-duplicate history messages — 2026-11-16
Structured hybrid_history_fallback metric events on pure-recency fallback — 2026-11-17
Structured hybrid_history_diversity_skipped metric events — 2026-11-18
Optional cross-channel history for hybrid retrieval — 2026-11-19
Structured hybrid_history_cross_channel_included metric events — 2026-11-19
Channel label in history prompt when cross-channel enabled — 2026-11-20
Sender name label in history prompt lines — 2026-11-21
Configurable per-line character limit and optional subject inclusion in history prompts — 2026-11-22
Restored full implementation after placeholder regression; added hybrid_history_prompt_length metric — 2026-11-24
Average score included in hybrid_history_selection metric — 2026-11-25
Structured hybrid_history_min_score_filtered metric events — 2026-11-26
Average age of selected messages included in hybrid_history_selection metric — 2026-11-27

## Context

The Twin Engine (`TwinEngineService._load_context` and the LangGraph `load_context_node`) currently loads the 5 most recent messages from the same sender + channel as short-term conversational memory. This is simple, deterministic, and avoids external embedding dependencies for the default path.

As conversation histories grow, pure recency can miss relevant earlier turns (e.g., a price question from two weeks ago). pgvector is already present in the schema, but no retrieval layer uses it yet for message history.

## Decision

Keep the existing recency window (limit=5) as the production default. Introduce a lightweight hybrid scorer that can be enabled later:

1. Candidate pool: last N messages from the same sender+channel (N configurable via `hybrid_history_pool_size`, default 20). Optionally from other channels with the same sender when `hybrid_history_cross_channel=true`.
2. Score = recency_weight * recency_decay + overlap_weight * simple_token_overlap with the incoming message (weights configurable via `hybrid_history_recency_weight` / `hybrid_history_overlap_weight`, defaults 0.7 / 0.3; normalized if they do not sum to 1).
3. Recency component is rank-based by default. Optionally (`hybrid_history_use_time_based_recency=true`) use exponential decay from actual message age with configurable half-life (`hybrid_history_recency_half_life_days`, default 7).
4. Select top K after scoring (K configurable via `hybrid_history_top_k`, default 5), optionally filtered by a minimum score (`hybrid_history_min_score`, default 0.0).
5. Optionally apply a diversity filter (`hybrid_history_diversity_threshold`, default 0.0 = disabled): greedy selection skips messages whose token overlap with any already-selected message exceeds the threshold. Reduces near-duplicates in the returned history. Emits a structured metric when skips occur.
6. Fall back to pure recency if the pool is small, scoring fails, or no messages meet the min score.
7. Optionally limit the rendered history prompt length (`hybrid_history_prompt_max_chars`, default 0 = unlimited) to protect against token overflow; emits a truncation metric when applied.
8. Emit structured fallback metrics when falling back to pure recency.
9. When cross-channel is enabled and selected messages come from other channels, emit a structured `hybrid_history_cross_channel_included` metric with the count.
10. When cross-channel is enabled, include the source channel in each history prompt line (e.g. `[2h ago | gmail]`) so the LLM has channel context.
11. Always include the sender_name in each history prompt line when available (e.g. `[2h ago | gmail | Alice]`) for better multi-party grounding.
12. Limit each history line's content preview to `hybrid_history_line_max_chars` (default 300) to control prompt size. Optionally include email subject from `channel_metadata` when present (e.g. `subj:Meeting follow-up`).
13. Always emit a structured `hybrid_history_prompt_length` metric with the final character count for prompt size monitoring.
14. The selection metric includes `avg_score` of the selected messages for quality observability.
15. When messages are filtered by min_score, emit a structured `hybrid_history_min_score_filtered` metric with the count and include `filtered_count` in the selection metric.
16. The selection metric includes `avg_age_days` of the selected messages (when timestamps are available) for recency observability.

No new dependencies. Token overlap uses the same `_extract_reference_tokens` helper already used for briefing matching. As of 2026-11-05 the helper filters a small English stopword set so overlap focuses on content words.

As of 2026-11-06 / 2026-11-07 / 2026-11-08, history prompts include richer relative timestamps (just now, Xm ago, Xh ago, yesterday, Xd ago, last week) for better LLM grounding, and hybrid mode logs top scores for observability.

As of 2026-11-14, hybrid selection always emits a structured INFO log (`metric=hybrid_history_selection`) with pool size, qualified count, selected count, top score, min_score, diversity_threshold, cross_channel, and cross_channel_count for easy dashboarding.

As of 2026-11-15, history prompts can be length-limited and emit `metric=hybrid_history_prompt_truncated` when truncated.

As of 2026-11-16, an optional diversity filter reduces redundant near-duplicate messages in the selected history when the threshold is set > 0.

As of 2026-11-17, fallbacks to pure recency emit `metric=hybrid_history_fallback` with reason (exception or min_score_not_met).

As of 2026-11-18, when the diversity filter skips messages it emits `metric=hybrid_history_diversity_skipped` with skipped_count.

As of 2026-11-19, an optional cross-channel mode (`hybrid_history_cross_channel=true`) lets the hybrid pool include messages from other channels with the same sender, improving multi-channel digital twin context. Default remains same-channel only. When cross-channel messages are selected, `metric=hybrid_history_cross_channel_included` is emitted with the count.

As of 2026-11-20, when cross-channel mode is enabled the history prompt includes the channel name on each line so the model can distinguish context sources.

As of 2026-11-21, history prompt lines include the sender_name when available, improving grounding for conversations involving named participants.

As of 2026-11-22, each history line is limited to a configurable character count (`hybrid_history_line_max_chars`, default 300) and may optionally include the email subject from channel metadata for better context without exceeding prompt budgets.

As of 2026-11-24, the full implementation was restored after a placeholder regression, and a new `hybrid_history_prompt_length` metric is always emitted for prompt size observability.

As of 2026-11-25, the selection metric includes the average score of selected messages to help monitor retrieval quality.

As of 2026-11-26, when the min_score filter excludes messages a structured `hybrid_history_min_score_filtered` metric is emitted with the count, and the selection metric includes `filtered_count` for better filter-impact observability.

As of 2026-11-27, the selection metric includes `avg_age_days` of selected messages (when timestamps available) to monitor how recent the retrieved context is.

Semantic retrieval via pgvector embeddings remains a future phase once a local or BYOK embedding model is configured (consistent with the LiteLLM draft path).

## Consequences

### Positive
- Better grounding for longer conversations without changing the HITL or safety contracts.
- Zero-risk default (current behavior unchanged until a feature flag is flipped).
- Reuses existing helpers and database queries.
- Stopword filtering improves precision of the token-overlap signal.
- Richer relative timestamps and score logging improve debuggability and draft quality.
- Pool size, top-K, scoring weights, (optionally) time-based recency, min score, prompt length, diversity threshold, cross-channel, line length, and subject inclusion are now tunable without code changes.
- Min score improves precision by excluding weakly related context.
- Diversity threshold improves context quality by reducing near-duplicate messages.
- Cross-channel option improves relevance for users who interact across Instagram, Gmail, etc.
- Channel labels in the prompt give the LLM explicit source context when multi-channel history is used.
- Sender name labels in the prompt give the LLM explicit participant context.
- Per-line character limits and optional subject inclusion give finer control over prompt size and context richness.
- Structured selection (now with avg_score, filtered_count, and avg_age_days), truncation, fallback, diversity-skip, cross-channel, min-score-filtered, and prompt-length metrics enable quality monitoring and alerting on context retrieval and prompt size.
- Prompt length limit protects downstream LLM calls from context overflow.
- Fallback, diversity, cross-channel, and min-score filter metrics make hybrid reliability and filter impact observable.
- Average score, filtered count, and average age in selection metric make it easier to detect when hybrid retrieval is selecting low-relevance, heavily filtered, or overly stale context.

### Negative / Trade-offs
- Token overlap is a weak proxy for semantics; true embeddings will be better later.
- Slightly more CPU on context load (still negligible).
- Time-based mode depends on accurate `created_at` timestamps.
- Aggressive min_score may reduce context volume (mitigated by pure-recency fallback).
- Aggressive prompt truncation may drop useful history (operators should set the limit based on model context window).
- Aggressive diversity threshold may drop useful but similar messages (operators should tune based on conversation style).
- Cross-channel mode may surface context from unrelated conversations if the sender is shared; keep default off and tune carefully.
- Channel, sender, subject labels and line truncation add a few tokens or may clip content; tune based on model context.

## Alternatives Considered

1. Full vector store immediately — rejected for MVP; adds latency, cost, and failure modes before the product has measured draft quality with a real model.
2. Sliding window only — current state; insufficient for multi-turn product questions.
3. External memory service — overkill for the self-hosted digital-twin use case.

## Follow-ups

- Implement the hybrid scorer behind `FEATURE_HYBRID_HISTORY=true`. **Done 2026-11-03.**
- Add a unit test that verifies a relevant older message outranks a recent irrelevant one. **Done 2026-11-04.**
- Filter common stopwords in token overlap for higher precision. **Done 2026-11-05.**
- Enrich history prompt with relative timestamps + hybrid score debug logging. **Done 2026-11-06 / restored 2026-11-07.**
- Richer relative time labels (yesterday, last week). **Done 2026-11-08.**
- Make candidate pool size configurable. **Done 2026-11-09.**
- Make top-K selection configurable. **Done 2026-11-10.**
- Make scoring weights configurable. **Done 2026-11-11.**
- Optional time-based (age-based exponential) recency instead of rank. **Done 2026-11-12.**
- Optional minimum hybrid score threshold with fallback. **Done 2026-11-13.**
- Structured hybrid_history_selection metric events. **Done 2026-11-14.**
- Optional history prompt character limit with truncation metric. **Done 2026-11-15.**
- Optional diversity threshold to reduce near-duplicate history messages. **Done 2026-11-16.**
- Structured hybrid_history_fallback metric events on pure-recency fallback. **Done 2026-11-17.**
- Structured hybrid_history_diversity_skipped metric events. **Done 2026-11-18.**
- Optional cross-channel history for hybrid retrieval. **Done 2026-11-19.**
- Structured hybrid_history_cross_channel_included metric events. **Done 2026-11-19.**
- Include channel label in history prompt when cross-channel is enabled. **Done 2026-11-20.**
- Include sender name in history prompt lines. **Done 2026-11-21.**
- Configurable per-line character limit (`hybrid_history_line_max_chars`) and optional subject inclusion. **Done 2026-11-22.**
- Restore full implementation after placeholder regression + emit hybrid_history_prompt_length metric. **Done 2026-11-24.**
- Include average score in hybrid_history_selection metric. **Done 2026-11-25.**
- Emit structured hybrid_history_min_score_filtered metric and include filtered_count in selection. **Done 2026-11-26.**
- Include average age of selected messages in hybrid_history_selection metric. **Done 2026-11-27.**
- Later: optional embedding column on `messages` + cosine search when an embedding provider is configured.

## References

- `src/backend/app/services/twin_engine.py` (`_load_context`, `_load_hybrid_history`, `_score_history_message`, `_extract_reference_tokens`, `_token_overlap`, `_build_prompts`, `_build_history_prompt`, `_format_relative_time`)
- `src/backend/app/services/twin_langgraph.py` (`load_context_node`)
- `src/backend/app/config.py` (`hybrid_history_pool_size`, `hybrid_history_top_k`, `hybrid_history_recency_weight`, `hybrid_history_overlap_weight`, `hybrid_history_use_time_based_recency`, `hybrid_history_recency_half_life_days`, `hybrid_history_min_score`, `hybrid_history_prompt_max_chars`, `hybrid_history_diversity_threshold`, `hybrid_history_cross_channel`, `hybrid_history_line_max_chars`)
- `docs/05-technical/SELPH_Database-Schema.md` (pgvector availability)
- `src/backend/tests/test_hybrid_history.py`
- `src/backend/tests/test_hybrid_history_sender_label.py`
- `src/backend/tests/test_hybrid_history_min_score_filtered.py`
- `src/backend/tests/test_hybrid_history_avg_age.py`
