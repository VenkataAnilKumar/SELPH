"""API-process `.delay()` calls must target the configured broker, not Celery's AMQP default."""

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
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=120
    )
    assert out.returncode == 0 and "ok" in out.stdout, out.stderr[-800:]
