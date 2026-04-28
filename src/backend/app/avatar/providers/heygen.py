"""HeyGen provider adapter for future production avatar cloning."""

import logging

from app.avatar.base import AvatarProvider, AvatarSynthesisRequest, AvatarSynthesisResult

logger = logging.getLogger(__name__)


class HeyGenAvatarProvider(AvatarProvider):
    """Phase 7 foundation adapter.

    This validates config and request prerequisites and returns a structured
    not-configured/not-implemented response for PR A foundation.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key or ""

    @property
    def provider_name(self) -> str:
        return "heygen"

    def synthesize(self, request: AvatarSynthesisRequest) -> AvatarSynthesisResult:
        if not self._api_key:
            return AvatarSynthesisResult(
                ok=False,
                provider=self.provider_name,
                error="HEYGEN_API_KEY is not configured",
            )

        if not request.avatar_model_id:
            return AvatarSynthesisResult(
                ok=False,
                provider=self.provider_name,
                error="avatar_model_id is required for HeyGen synthesis",
            )

        logger.info("HeyGen adapter foundation called for draft=%s", request.draft_id)
        return AvatarSynthesisResult(
            ok=False,
            provider=self.provider_name,
            error="HeyGen synthesis implementation is planned in Phase 7 PR B",
        )
