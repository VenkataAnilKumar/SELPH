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

## Context

The Twin Engine (`TwinEngineService._load_context` and the LangGraph `load_context_node`) currently loads the 5 most recent messages from the same sender + channel as short-term conversational memory. This is simple, deterministic, and avoids external embedding dependencies for the default path.

As conversation histories grow, pure recency can miss relevant earlier turns (e.g., a price question from two weeks ago). pgvector is already present in the schema, but no retrieval layer uses it yet for message history.

## Decision

Keep the existing recency window (limit=5) as the production default. Introduce a lightweight hybrid scorer that can be enabled later:

1. Candidate pool: last N messages from the same sender+channel (N configurable via `hybrid_history_pool_size`, default 20).
2. Score = recency_weight * recency_decay + overlap_weight * simple_token_overlap with the incoming message (weights configurable via `hybrid_history_recency_weight` / `hybrid_history_overlap_weight`, defaults 0.7 / 0.3; normalized if they do not sum to 1).
3. Recency component is rank-based by default. Optionally (`hybrid_history_use_time_based_recency=true`) use exponential decay from actual message age with configurable half-life (`hybrid_history_recency_half_life_days`, default 7).
4. Select top K after scoring (K configurable via `hybrid_history_top_k`, default 5), optionally filtered by a minimum score (`hybrid_history_min_score`, default 0.0).
5. Fall back to pure recency if the pool is small, scoring fails, or no messages meet the min score.

No new dependencies. Token overlap uses the same `_extract_reference_tokens` helper already used for briefing matching. As of 2026-11-05 the helper filters a small English stopword set so overlap focuses on content words.

As of 2026-11-06 / 2026-11-07 / 2026-11-08, history prompts include richer relative timestamps (just now, Xm ago, Xh ago, yesterday, Xd ago, last week) for better LLM grounding, and hybrid mode logs top scores for observability.

As of 2026-11-14, hybrid selection always emits a structured INFO log (`metric=hybrid_history_selection`) with pool size, qualified count, selected count, top score, and min_score for easy dashboarding.

Semantic retrieval via pgvector embeddings remains a future phase once a local or BYOK embedding model is configured (consistent with the LiteLLM draft path).

## Consequences

### Positive
- Better grounding for longer conversations without changing the HITL or safety contracts.
- Zero-risk default (current behavior unchanged until a feature flag is flipped).
- Reuses existing helpers and database queries.
- Stopword filtering improves precision of the token-overlap signal.
- Richer relative timestamps and score logging improve debuggability and draft quality.
- Pool size, top-K, scoring weights, (optionally) time-based recency, and min score are now tunable without code changes.
- Min score improves precision by excluding weakly related context.
- Structured selection metrics enable quality monitoring and alerting on context retrieval.

### Negative / Trade-offs
- Token overlap is a weak proxy for semantics; true embeddings will be better later.
- Slightly more CPU on context load (still negligible).
- Time-based mode depends on accurate `created_at` timestamps.
- Aggressive min_score may reduce context volume (mitigated by pure-recency fallback).

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
- Later: optional embedding column on `messages` + cosine search when an embedding provider is configured.

## References

- `src/backend/app/services/twin_engine.py` (`_load_context`, `_load_hybrid_history`, `_score_history_message`, `_extract_reference_tokens`, `_build_prompts`, `_build_history_prompt`, `_format_relative_time`)
- `src/backend/app/services/twin_langgraph.py` (`load_context_node`)
- `src/backend/app/config.py` (`hybrid_history_pool_size`, `hybrid_history_top_k`, `hybrid_history_recency_weight`, `hybrid_history_overlap_weight`, `hybrid_history_use_time_based_recency`, `hybrid_history_recency_half_life_days`, `hybrid_history_min_score`)
- `docs/05-technical/SELPH_Database-Schema.md` (pgvector availability)
- `src/backend/tests/test_hybrid_history.py`
