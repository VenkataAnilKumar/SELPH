"""Base interfaces for voice synthesis providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceSynthesisRequest:
    """Normalized request payload for voice synthesis."""

    text: str
    voice_model_id: str | None = None
    user_id: str | None = None
    draft_id: str | None = None


@dataclass
class VoiceSynthesisResult:
    """Normalized synthesis response for task orchestration."""

    ok: bool
    provider: str
    audio_url: str | None = None
    error: str | None = None


class VoiceProvider(ABC):
    """Abstract provider contract for voice synthesis backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        raise NotImplementedError
