"""Voice synthesis provider abstraction and registry."""

from app.voice.base import VoiceProvider, VoiceSynthesisRequest, VoiceSynthesisResult
from app.voice.registry import get_voice_provider

__all__ = [
    "VoiceProvider",
    "VoiceSynthesisRequest",
    "VoiceSynthesisResult",
    "get_voice_provider",
]
