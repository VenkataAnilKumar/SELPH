# SELPH — Observability

The API exposes Prometheus metrics at `GET /metrics` (no extra dependencies). Set `METRICS_TOKEN`
and scrape with `Authorization: Bearer <token>`; in production `/metrics` is hidden without a token.

```yaml
scrape_configs:
  - job_name: selph-api
    metrics_path: /metrics
    authorization: { type: Bearer, credentials: "<METRICS_TOKEN>" }
    static_configs: [{ targets: ["api:8000"] }]
```

## Metrics

| Metric | Type | Meaning |
|---|---|---|
| `selph_http_requests_total{method,route,status}` | counter | Requests by route *template* (no IDs) |
| `selph_http_request_duration_seconds{method,route}` | histogram | API latency |
| `selph_messages_ingested_total{channel}` | counter | Inbound messages stored |
| `selph_message_routing_total{action}` | counter | `notify_user`, `notify_user_force_review`, `direct_notify` (VIP), `skipped_manual_pause`, `use_crisis_template` |
| `selph_drafts_created_total{source,moderation}` | counter | Drafts by `deterministic`/`llm` and `passed`/`flagged` |
| `selph_draft_pipeline_duration_seconds{source}` | histogram | Twin pipeline latency per draft |
| `selph_draft_decisions_total{action}` | counter | Approval funnel: `approve`, `edit`, `reject`, `skip` |
| `selph_moderation_flags_total{category}` | counter | Drafts flagged per category (`prompt_injection`, `sensitive_incoming`, `hard_block_*`, ...) |
| `selph_drafts{status}` | gauge | Current drafts per status (`pending_approval` = review backlog) |
| `selph_celery_queue_depth{queue}` | gauge | Queue lag per Celery queue |
| `selph_broker_up` | gauge | 1 if the broker is reachable |

Counters are per process; scrape every replica (or use Prometheus multiprocess mode for several workers per container).

## SLO queries

```promql
# p95 API latency (5m)
histogram_quantile(0.95, sum by (le) (rate(selph_http_request_duration_seconds_bucket[5m])))

# p95 draft generation latency
histogram_quantile(0.95, sum by (le) (rate(selph_draft_pipeline_duration_seconds_bucket[5m])))

# 5xx error rate
sum(rate(selph_http_requests_total{status=~"5.."}[5m])) / sum(rate(selph_http_requests_total[5m]))

# Approval funnel: share of decisions approved without edits (the product's core quality signal)
sum(increase(selph_draft_decisions_total{action="approve"}[7d])) / sum(increase(selph_draft_decisions_total[7d]))

# Moderation false-positive watch: share of drafts flagged
sum(rate(selph_drafts_created_total{moderation="flagged"}[1h])) / sum(rate(selph_drafts_created_total[1h]))

# Queue lag
max by (queue) (selph_celery_queue_depth)
```

## Suggested alerts

| Alert | Expression | For |
|---|---|---|
| API p95 slow | p95 API latency > 1s | 10m |
| 5xx rate high | 5xx error rate > 2% | 5m |
| Draft pipeline slow | p95 draft latency > 10s | 10m |
| Queue backing up | `selph_celery_queue_depth > 100` | 10m |
| Broker down | `selph_broker_up == 0` | 2m |
| Review backlog | `selph_drafts{status="pending_approval"} > 200` | 1h |
| Approval quality drop | weekly approved-without-edit share < 40% | 1d |

## Audit events

Every draft also writes a structured audit event (`audit_logs`, `action = 'twin_engine_audit'`) with `event_type`
(`ready_for_hitl` or `flagged_for_review`), `risk_band`, `priority_score`, `hitl_priority`, `latency_band`,
`graph_duration_ms`, `generation_source`, `generation_attempts`, `moderation_flags`, `context_signals` and
`error_category`. Use it to rank the review queue and to triage slow or failing generations:

```sql
SELECT details->>'event_type' AS event, details->>'risk_band' AS risk, count(*)
FROM audit_logs WHERE action = 'twin_engine_audit' AND created_at > now() - interval '1 day'
GROUP BY 1, 2 ORDER BY 3 DESC;
```

Account erasure keeps these rows anonymized (identifying details are stripped).

