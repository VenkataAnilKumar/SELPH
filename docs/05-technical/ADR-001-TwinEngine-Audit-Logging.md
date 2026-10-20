# ADR-001: TwinEngine Audit Logging Node

## Status

Accepted — 2026-10-20

## Context

SELPH's Twin Engine is being migrated to a LangGraph StateGraph (`src/backend/app/services/twin_langgraph.py`) to support interruptible human-in-the-loop (HITL) approval. Safety requires that every draft path — both successful HITL-ready and moderation-flagged — produce a structured, queryable audit event.

Recent commits added `audit_log_node` that standardizes the final result with an `audit` payload (event_type, flags, risk, confidence, timestamp). This ADR records the design decision.

## Decision

Introduce a dedicated terminal `audit_log` node that:

1. Runs after both `process_decision` (HITL path) and `flag_for_review` (safety path).
2. Builds a canonical `audit_event` dict containing:
   - `event_type`: `ready_for_hitl` | `flagged_for_review`
   - identifiers (`message_id`, `user_id`)
   - moderation and confidence signals
   - recommended action and status
   - ISO timestamp and optional `error`
3. Attaches the audit payload to the graph `result` so callers and checkpointers receive it.
4. Emits a structured log line for external observability pipelines.

Error states currently route to `flag_for_review` (via `route_after_moderation`) and still receive an audit event. This keeps the graph simple while ensuring no path ends without an audit record.

## Consequences

### Positive
- Consistent, machine-readable audit trail for every twin draft.
- Aligns with the safety and compliance goals in `docs/04-safety/` and the System Architecture.
- Enables future dashboard queries and alerting without changing node contracts.
- Non-breaking for existing sequential `TwinEngineService` path.

### Negative / Trade-offs
- Extra node adds a small amount of graph complexity.
- Audit is currently log + in-memory result; durable persistence (e.g., writing to `audit_logs` table) is a follow-up.
- Error paths share the flagged event type; a distinct `error` event type can be added later if needed.

## Alternatives Considered

1. **Inline audit inside each terminal node** — rejected; duplicates logic and risks drift.
2. **Post-graph middleware** — rejected for LangGraph; the graph itself is the single source of truth.
3. **Rely solely on existing ModerationService logs** — insufficient; lacks the full HITL context and standardized schema.

## Follow-ups

- Persist `audit_event` to the `audit_logs` table (or LangGraph checkpoint metadata).
- Add Prometheus / structured metrics counters for event types and risk scores.
- Consider a distinct `event_type=error` when `state.error` is set.
- Wire PostgresSaver / RedisSaver in production compile path (already noted in code).

## References

- `src/backend/app/services/twin_langgraph.py`
- `docs/05-technical/SELPH_System-Architecture.md` (Twin Engine section)
- Recent commits: `feat(agents): add audit_log_node ...` (2026-10-19)
