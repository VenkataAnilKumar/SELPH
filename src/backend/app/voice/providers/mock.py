"""Deterministic mock voice provider for local development and tests."""

from app.voice.base import VoiceProvider, VoiceSynthesisRequest, VoiceSynthesisResult


class MockVoiceProvider(VoiceProvider):
    """Returns a deterministic mock URL with no external calls."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        draft_id = request.draft_id or "unknown"
        return VoiceSynthesisResult(
            ok=True,
            provider=self.provider_name,
            audio_url=f"mock://voice/{draft_id}.mp3",
        )
