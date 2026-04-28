"""Provider registry for voice synthesis backends."""

from app.config import get_settings
from app.voice.base import VoiceProvider
from app.voice.providers.mock import MockVoiceProvider
from app.voice.providers.elevenlabs import ElevenLabsVoiceProvider


def get_voice_provider(provider_name: str | None = None) -> VoiceProvider:
    """Return a concrete provider instance based on config or explicit name."""
    settings = get_settings()
    selected = (provider_name or settings.voice_provider or "mock").strip().lower()

    if selected == "mock":
        return MockVoiceProvider()
    if selected == "elevenlabs":
        return ElevenLabsVoiceProvider(api_key=settings.elevenlabs_api_key)

    raise ValueError(f"Unsupported voice provider '{selected}'")
