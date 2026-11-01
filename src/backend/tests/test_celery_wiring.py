"""API-process `.delay()` calls must target the configured broker, not Celery's AMQP default."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def test_api_process_tasks_use_configured_broker():
    code = textwrap.dedent(
        """
        from app.main import app  # what uvicorn imports
        from app.config import get_settings
        from app.tasks.push_notifications import notify_draft_ready
        from app.tasks.voice_synthesis import synthesize_voice

        broker = get_settings().celery_broker_url
        assert notify_draft_ready.app.conf.broker_url == broker, notify_draft_ready.app.conf.broker_url
        assert synthesize_voice.app.conf.broker_url == broker
        assert broker.startswith("redis://")
        print("ok")
        """
    )
    # Fresh interpreter: proves the wiring comes from the app import path itself.
    env = {k: v for k, v in os.environ.items() if not k.startswith("CELERY_")}  # real defaults, not the test broker
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=120, env=env
    )
    assert out.returncode == 0 and "ok" in out.stdout, out.stderr[-800:]


def test_publishing_never_hangs_when_redis_is_down():
    """A Redis outage (broker AND result backend) must fail a publish fast, not freeze the request."""
    code = textwrap.dedent(
        """
        import time
        from app.main import app
        from app.tasks.push_notifications import notify_draft_ready

        elapsed = []
        for _ in range(3):
            start = time.time()
            try:
                notify_draft_ready.delay("u", "d")
            except Exception:
                pass
            elapsed.append(time.time() - start)
        assert max(elapsed) < 6, elapsed
        print("ok", [round(e, 1) for e in elapsed])
        """
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("CELERY_")}
    env["CELERY_BROKER_URL"] = "redis://127.0.0.1:1/1"       # nothing listens here
    env["CELERY_RESULT_BACKEND"] = "redis://127.0.0.1:1/2"
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=60, env=env)
    assert out.returncode == 0 and "ok" in out.stdout, out.stdout + out.stderr[-600:]
