# ADR-002: Short-Term Memory Retrieval for Twin Context

## Status

Implemented — 2026-11-03 (feature flag default off)

## Context

The Twin Engine (`TwinEngineService._load_context` and the LangGraph `load_context_node`) currently loads the 5 most recent messages from the same sender + channel as short-term conversational memory. This is simple, deterministic, and avoids external embedding dependencies for the default path.

As conversation histories grow, pure recency can miss relevant earlier turns (e.g., a price question from two weeks ago). pgvector is already present in the schema, but no retrieval layer uses it yet for message history.

## Decision

Keep the existing recency window (limit=5) as the production default. Introduce a lightweight hybrid scorer that can be enabled later:

1. Candidate pool: last N=20 messages from the same sender+channel (still cheap).
2. Score = 0.7 * recency_decay + 0.3 * simple_token_overlap with the incoming message.
3. Select top 5 after scoring.
4. Fall back to pure recency if the pool is small or scoring fails.

No new dependencies. Token overlap uses the same `_extract_reference_tokens` helper already used for briefing matching. As of 2026-11-05 the helper filters a small English stopword set so overlap focuses on content words.

As of 2026-11-06, history prompts include relative timestamps for better LLM grounding, and hybrid mode logs top scores for observability.

Semantic retrieval via pgvector embeddings remains a future phase once a local or BYOK embedding model is configured (consistent with the LiteLLM draft path).

## Consequences

### Positive
- Better grounding for longer conversations without changing the HITL or safety contracts.
- Zero-risk default (current behavior unchanged until a feature flag is flipped).
- Reuses existing helpers and database queries.
- Stopword filtering improves precision of the token-overlap signal.
- Relative timestamps and score logging improve debuggability and draft quality.

### Negative / Trade-offs
- Token overlap is a weak proxy for semantics; true embeddings will be better later.
- Slightly more CPU on context load (still negligible).

## Alternatives Considered

1. Full vector store immediately — rejected for MVP; adds latency, cost, and failure modes before the product has measured draft quality with a real model.
2. Sliding window only — current state; insufficient for multi-turn product questions.
3. External memory service — overkill for the self-hosted digital-twin use case.

## Follow-ups

- Implement the hybrid scorer behind `FEATURE_HYBRID_HISTORY=true`. **Done 2026-11-03.**
- Add a unit test that verifies a relevant older message outranks a recent irrelevant one. **Done 2026-11-04.**
- Filter common stopwords in token overlap for higher precision. **Done 2026-11-05.**
- Enrich history prompt with relative timestamps + hybrid score debug logging. **Done 2026-11-06.**
- Later: optional embedding column on `messages` + cosine search when an embedding provider is configured.

## References

- `src/backend/app/services/twin_engine.py` (`_load_context`, `_load_hybrid_history`, `_score_history_message`, `_extract_reference_tokens`, `_build_prompts`)
- `src/backend/app/services/twin_langgraph.py` (`load_context_node`)
- `docs/05-technical/SELPH_Database-Schema.md` (pgvector availability)
- `src/backend/tests/test_hybrid_history.py`
