"""Avatar synthesis provider abstraction and registry."""

from app.avatar.base import AvatarProvider, AvatarSynthesisRequest, AvatarSynthesisResult
from app.avatar.registry import get_avatar_provider

__all__ = [
    "AvatarProvider",
    "AvatarSynthesisRequest",
    "AvatarSynthesisResult",
    "get_avatar_provider",
]
