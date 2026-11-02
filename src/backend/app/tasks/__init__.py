"""
Celery tasks
"""

# Importing the configured Celery app makes it the process-wide default, so `.delay()` calls made
# from the API process publish to the configured broker (Redis) instead of Celery's built-in
# AMQP default. Must run before any task module is used.
from app.celery_app import celery_app  # noqa: F401

from app.tasks.draft_generation import (
    generate_draft_for_message,
    process_draft_generation,
)

from app.tasks.message_processing import (
    process_incoming_message,
    batch_process_messages,
)

from app.tasks.send_reply import (
    send_channel_reply,
)

from app.tasks.voice_synthesis import (
    synthesize_voice,
)

from app.tasks.avatar_generation import (
    generate_avatar,
)
from app.tasks.proactive_scan import (
    run_proactive_scan,
)
from app.tasks.surge_check import (
    run_surge_check,
)
from app.tasks.style_evolution import (
    run_style_evolution,
)
from app.tasks.t2t_negotiation import (
    run_t2t_maintenance,
)

__all__ = [
    "generate_draft_for_message",
    "process_draft_generation",
    "process_incoming_message",
    "batch_process_messages",
    "send_channel_reply",
    "synthesize_voice",
    "generate_avatar",
    "run_proactive_scan",
    "run_surge_check",
    "run_style_evolution",
    "run_t2t_maintenance",
]
