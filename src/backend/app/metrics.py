"""
Dependency-free Prometheus metrics for SELPH.

Exposes request latency (p95 via histogram), draft pipeline latency, the approval funnel,
moderation outcomes, and queue depth in Prometheus text format at GET /metrics.

Counters/histograms live in-process (per worker). Scrape every replica, or use a
Prometheus multiprocess setup if you run several uvicorn workers per container.
Labels are low-cardinality on purpose: route *templates* (never raw paths or IDs).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Iterable

LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
DRAFT_BUCKETS = (0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)

# Celery queues the app publishes to; depth is read from Redis at scrape time.
QUEUES = ("celery", "draft_generation", "message_processing", "voice_synthesis", "avatar_generation")


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _labels(names: tuple[str, ...], values: tuple) -> str:
    if not names:
        return ""
    return "{" + ",".join(f'{n}="{_escape(v)}"' for n, v in zip(names, values)) + "}"


class Counter:
    def __init__(self, name: str, help_text: str, labelnames: tuple[str, ...] = ()):
        self.name, self.help, self.labelnames = name, help_text, labelnames
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, *labelvalues, amount: float = 1.0) -> None:
        with self._lock:
            self._values[tuple(str(v) for v in labelvalues)] += amount

    def value(self, *labelvalues) -> float:
        return self._values.get(tuple(str(v) for v in labelvalues), 0.0)

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} counter"
        with self._lock:
            items = sorted(self._values.items())
        for labelvalues, val in items:
            yield f"{self.name}{_labels(self.labelnames, labelvalues)} {val:g}"


class Histogram:
    def __init__(self, name: str, help_text: str, buckets: tuple[float, ...], labelnames: tuple[str, ...] = ()):
        self.name, self.help, self.buckets, self.labelnames = name, help_text, buckets, labelnames
        self._counts: dict[tuple, list[int]] = {}
        self._sums: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value: float, *labelvalues) -> None:
        key = tuple(str(v) for v in labelvalues)
        with self._lock:
            counts = self._counts.setdefault(key, [0] * (len(self.buckets) + 1))
            for i, bound in enumerate(self.buckets):
                if value <= bound:
                    counts[i] += 1
            counts[-1] += 1  # +Inf / total
            self._sums[key] += value

    def count(self, *labelvalues) -> int:
        counts = self._counts.get(tuple(str(v) for v in labelvalues))
        return counts[-1] if counts else 0

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} histogram"
        with self._lock:
            snapshot = {k: (list(v), self._sums[k]) for k, v in self._counts.items()}
        for key, (counts, total) in sorted(snapshot.items()):
            for bound, c in zip(self.buckets, counts):
                names = self.labelnames + ("le",)
                yield f"{self.name}_bucket{_labels(names, key + (f'{bound:g}',))} {c}"
            yield f"{self.name}_bucket{_labels(self.labelnames + ('le',), key + ('+Inf',))} {counts[-1]}"
            yield f"{self.name}_sum{_labels(self.labelnames, key)} {total:g}"
            yield f"{self.name}_count{_labels(self.labelnames, key)} {counts[-1]}"


# ── Metric definitions ───────────────────────────────────────────────────────

HTTP_REQUESTS = Counter("selph_http_requests_total", "HTTP requests", ("method", "route", "status"))
HTTP_LATENCY = Histogram("selph_http_request_duration_seconds", "HTTP request latency", LATENCY_BUCKETS, ("method", "route"))
MESSAGES = Counter("selph_messages_ingested_total", "Incoming messages stored", ("channel",))
ROUTING = Counter("selph_message_routing_total", "How incoming messages were routed", ("action",))
DRAFTS = Counter("selph_drafts_created_total", "Drafts created", ("source", "moderation"))
DRAFT_LATENCY = Histogram("selph_draft_pipeline_duration_seconds", "Twin pipeline latency per draft", DRAFT_BUCKETS, ("source",))
DECISIONS = Counter("selph_draft_decisions_total", "User decisions on drafts (approval funnel)", ("action",))
MODERATION_FLAGS = Counter("selph_moderation_flags_total", "Moderation flags raised", ("category",))

_ALL = (HTTP_REQUESTS, HTTP_LATENCY, MESSAGES, ROUTING, DRAFTS, DRAFT_LATENCY, DECISIONS, MODERATION_FLAGS)


def record_message(channel: str) -> None:
    MESSAGES.inc(channel)


def record_routing(action: str) -> None:
    ROUTING.inc(action or "unknown")


def record_draft(source: str | None, moderation_passed: bool, flags: list | None, latency_ms: float | None) -> None:
    source = source or "unknown"
    DRAFTS.inc(source, "passed" if moderation_passed else "flagged")
    if latency_ms is not None:
        DRAFT_LATENCY.observe(latency_ms / 1000.0, source)
    # Once per category per draft, so the counter answers "how many drafts were flagged for X".
    for category in {(flag or {}).get("category") or "uncategorized" for flag in flags or []}:
        MODERATION_FLAGS.inc(category)


def record_decision(action: str) -> None:
    DECISIONS.inc(action)


# ── HTTP middleware (pure ASGI: no response buffering) ───────────────────────

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.perf_counter()
        status_holder = {"code": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            template = getattr(route, "path", None) or "unmatched"
            if template != "/metrics":
                method = scope.get("method", "GET")
                HTTP_REQUESTS.inc(method, template, status_holder["code"])
                HTTP_LATENCY.observe(time.perf_counter() - start, method, template)


# ── Scrape-time gauges ───────────────────────────────────────────────────────

def _gauge(name: str, help_text: str, samples: list[tuple[str, float]]) -> list[str]:
    lines = [f"# HELP {name} {help_text}", f"# TYPE {name} gauge"]
    lines += [f"{name}{labels} {value:g}" for labels, value in samples]
    return lines


def queue_depths(redis_url: str) -> dict[str, int] | None:
    """Celery queue lengths from the broker; None when Redis is unreachable."""
    try:
        import redis

        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        return {q: int(client.llen(q)) for q in QUEUES}
    except Exception:
        return None


def render_metrics(db=None, broker_url: str | None = None) -> str:
    lines: list[str] = []
    for metric in _ALL:
        lines.extend(metric.render())

    if db is not None:
        try:
            from sqlalchemy import func
            from app.models import Draft

            rows = dict(db.query(Draft.status, func.count(Draft.id)).group_by(Draft.status).all())
            lines += _gauge(
                "selph_drafts",
                "Drafts currently in each status (pending = review backlog)",
                [(f'{{status="{_escape(k)}"}}', v) for k, v in sorted(rows.items())],
            )
        except Exception:
            pass

    if broker_url:
        depths = queue_depths(broker_url)
        if depths is None:
            lines += _gauge("selph_broker_up", "1 if the Celery broker is reachable", [("", 0)])
        else:
            lines += _gauge("selph_broker_up", "1 if the Celery broker is reachable", [("", 1)])
            lines += _gauge(
                "selph_celery_queue_depth",
                "Pending Celery tasks per queue (queue lag)",
                [(f'{{queue="{q}"}}', n) for q, n in sorted(depths.items())],
            )
    return "\n".join(lines) + "\n"
