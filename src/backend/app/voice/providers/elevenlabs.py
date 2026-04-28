"""ElevenLabs provider adapter for future production voice cloning."""

import logging

from app.voice.base import VoiceProvider, VoiceSynthesisRequest, VoiceSynthesisResult

logger = logging.getLogger(__name__)


class ElevenLabsVoiceProvider(VoiceProvider):
    """Phase 6 foundation adapter.

    This is intentionally conservative for PR A: it validates config and returns
    a structured not-configured/not-implemented response when prerequisites are
    missing.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key or ""

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        if not self._api_key:
            return VoiceSynthesisResult(
                ok=False,
                provider=self.provider_name,
                error="ELEVENLABS_API_KEY is not configured",
            )

        if not request.voice_model_id:
            return VoiceSynthesisResult(
                ok=False,
                provider=self.provider_name,
                error="voice_model_id is required for ElevenLabs synthesis",
            )

        logger.info("ElevenLabs adapter foundation called for draft=%s", request.draft_id)
        return VoiceSynthesisResult(
            ok=False,
            provider=self.provider_name,
            error="ElevenLabs synthesis implementation is planned in Phase 6 PR B",
        )
