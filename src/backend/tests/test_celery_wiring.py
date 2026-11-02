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


# ── a worker must be able to run every job the app publishes ─────────────────

def _fresh_python(code: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CELERY_")}
    out = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=BACKEND, capture_output=True,
                         text=True, timeout=120, env=env)
    assert out.returncode == 0, out.stderr[-800:]
    return out.stdout.strip()


def test_worker_registers_every_task_the_app_defines():
    """A worker imports only app.celery_app. Any task module it does not load gets 'unregistered task'
    and the job is discarded (this silently dropped push notifications)."""
    result = _fresh_python(
        """
        import importlib, pkgutil, json
        import app.tasks as pkg
        from app.celery_app import celery_app
        celery_app.loader.import_default_modules()           # what a worker does at boot
        registered = {n for n in celery_app.tasks if n.startswith(("app.", "tasks."))}

        defined = set()
        for mod in pkgutil.iter_modules(pkg.__path__):
            m = importlib.import_module(f"app.tasks.{mod.name}")
            for obj in vars(m).values():
                if hasattr(obj, "delay") and getattr(obj, "name", "").startswith(("app.", "tasks.")):
                    defined.add(obj.name)
        print(json.dumps({"missing": sorted(defined - registered), "defined": len(defined)}))
        """
    )
    import json

    data = json.loads(result)
    assert data["defined"] >= 12
    assert data["missing"] == [], f"worker would reject these tasks: {data['missing']}"


def test_worker_consumes_every_queue_tasks_publish_to():
    """Jobs published to a queue nobody consumes wait in Redis forever (delivery uses 'channels')."""
    import re
    from pathlib import Path

    from app.celery_app import WORKER_QUEUES

    published = set()
    for path in (BACKEND / "app" / "tasks").glob("*.py"):
        published |= set(re.findall(r'queue="([a-z_]+)"', path.read_text()))
    assert published, "expected tasks that declare a queue"
    assert published <= set(WORKER_QUEUES), f"queues without a consumer: {published - set(WORKER_QUEUES)}"

    # Every deployment recipe must consume the same queues.
    repo = BACKEND.parent.parent
    for compose in (repo / "docker-compose.yml", BACKEND / "docker-compose.yml"):
        text = compose.read_text()
        match = re.search(r"worker\b[^\n]*(?:--queues=|-Q )([a-z_,]+)", text)
        assert match, f"no worker queue list found in {compose}"
        assert set(match.group(1).split(",")) == set(WORKER_QUEUES), f"{compose.name}: {match.group(1)}"
    assert 'WORKER_QUEUES' in (BACKEND / "worker.py").read_text()   # the production entry point uses the shared list
