"""
Celery tasks
"""

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

__all__ = [
    "generate_draft_for_message",
    "process_draft_generation",
    "process_incoming_message",
    "batch_process_messages",
    "send_channel_reply",
    "synthesize_voice",
    "generate_avatar",
]
