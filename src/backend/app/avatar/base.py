"""Base interfaces for avatar synthesis providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AvatarSynthesisRequest:
    """Normalized request payload for avatar generation."""

    text: str
    avatar_model_id: str | None = None
    voice_audio_url: str | None = None
    user_id: str | None = None
    draft_id: str | None = None


@dataclass
class AvatarSynthesisResult:
    """Normalized avatar generation response for task orchestration."""

    ok: bool
    provider: str
    video_url: str | None = None
    error: str | None = None


class AvatarProvider(ABC):
    """Abstract provider contract for avatar synthesis backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, request: AvatarSynthesisRequest) -> AvatarSynthesisResult:
        raise NotImplementedError
