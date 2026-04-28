"""
Celery tasks
"""

from app.tasks.draft_generation import (
    generate_draft_for_message,
    process_draft_generation,
)

from app.tasks.message_processing import (
    process_incoming_message,
)

from app.tasks.voice_synthesis import (
    synthesize_voice,
)

from app.tasks.avatar_generation import (
    generate_avatar,
)

__all__ = [
    "generate_draft_for_message",
    "process_draft_generation",
    "process_incoming_message",
    "synthesize_voice",
    "generate_avatar",
]
