"""Provider registry for avatar synthesis backends."""

from app.avatar.base import AvatarProvider
from app.avatar.providers.mock import MockAvatarProvider
from app.avatar.providers.heygen import HeyGenAvatarProvider
from app.config import get_settings


def get_avatar_provider(provider_name: str | None = None) -> AvatarProvider:
    """Return a concrete avatar provider instance from config or explicit name."""
    settings = get_settings()
    selected = (provider_name or settings.avatar_provider or "mock").strip().lower()

    if selected == "mock":
        return MockAvatarProvider()
    if selected == "heygen":
        return HeyGenAvatarProvider(api_key=settings.heygen_api_key)

    raise ValueError(f"Unsupported avatar provider '{selected}'")
