"""Deterministic mock avatar provider for local development and tests."""

from app.avatar.base import AvatarProvider, AvatarSynthesisRequest, AvatarSynthesisResult


class MockAvatarProvider(AvatarProvider):
    """Returns a deterministic mock video URL with no external calls."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def synthesize(self, request: AvatarSynthesisRequest) -> AvatarSynthesisResult:
        draft_id = request.draft_id or "unknown"
        return AvatarSynthesisResult(
            ok=True,
            provider=self.provider_name,
            video_url=f"mock://avatar/{draft_id}.mp4",
        )
