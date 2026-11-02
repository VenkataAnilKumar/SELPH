"""
Fixed-window rate limiting for authentication endpoints.

Counts live in Redis so the limit holds across replicas and restarts. If Redis is
unreachable the limiter degrades to an in-process counter instead of failing open
or taking login down. In-process buckets are discarded once their window passes,
so memory stays bounded no matter how many distinct clients connect.
"""

from __future__ import annotations

import logging
import threading
import time

from app.config import get_settings

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60

_local: dict[str, tuple[int, int]] = {}  # key -> (window_id, count)
_local_lock = threading.Lock()
_redis_client = None
_redis_down_until = 0.0


def _redis():
    """Lazily create the Redis client; back off for 30s after a failure."""
    global _redis_client, _redis_down_until
    if time.time() < _redis_down_until:
        return None
    if _redis_client is None:
        try:
            import redis

            _redis_client = redis.Redis.from_url(
                get_settings().redis_url, socket_connect_timeout=0.3, socket_timeout=0.3
            )
        except Exception:
            _redis_down_until = time.time() + 30
            return None
    return _redis_client


def _mark_redis_down(exc: Exception) -> None:
    global _redis_client, _redis_down_until
    logger.warning("Rate limiter falling back to in-process counters: %s", exc)
    _redis_client = None
    _redis_down_until = time.time() + 30


def _hit_local(key: str, window_id: int) -> int:
    with _local_lock:
        if len(_local) > 10_000:  # opportunistic sweep of expired windows
            for k in [k for k, (w, _) in _local.items() if w != window_id]:
                del _local[k]
        w, count = _local.get(key, (window_id, 0))
        count = count + 1 if w == window_id else 1
        _local[key] = (window_id, count)
        return count


def hit(route: str, client_id: str, now: float | None = None) -> int:
    """Record one attempt and return how many fall inside the current window."""
    now = time.time() if now is None else now
    window_id = int(now // WINDOW_SECONDS)
    key = f"selph:rl:{route}:{client_id}:{window_id}"

    client = _redis()
    if client is not None:
        try:
            count = int(client.incr(key))
            if count == 1:
                client.expire(key, WINDOW_SECONDS * 2)
            return count
        except Exception as exc:
            _mark_redis_down(exc)
    return _hit_local(key, window_id)


def reset() -> None:
    """Clear in-process state (tests)."""
    global _redis_client, _redis_down_until
    with _local_lock:
        _local.clear()
    _redis_client = None
    _redis_down_until = 0.0
