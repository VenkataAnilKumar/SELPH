"""
Channel adapter registry.
Maps channel names → adapter instances.

Usage:
    from app.channels.registry import get_adapter
    adapter = get_adapter("instagram_dm")
"""

from app.channels.base import ChannelAdapter
from app.channels.instagram import InstagramAdapter
from app.channels.gmail import GmailAdapter

# Singleton adapter instances (stateless — all config loaded at call time via get_settings())
_ADAPTERS: dict[str, ChannelAdapter] = {
    "instagram": InstagramAdapter(),
    "instagram_dm": InstagramAdapter(),
    "gmail": GmailAdapter(),
}


def get_adapter(channel: str) -> ChannelAdapter:
    """
    Return the adapter for a given channel name.

    Args:
        channel: Channel identifier, e.g. 'instagram', 'instagram_dm', 'gmail'.

    Raises:
        ValueError: If no adapter is registered for the given channel name.
    """
    adapter = _ADAPTERS.get(channel.lower().strip())
    if not adapter:
        raise ValueError(
            f"No adapter registered for channel '{channel}'. "
            f"Available: {', '.join(_ADAPTERS.keys())}"
        )
    return adapter


def list_channels() -> list[str]:
    """Return deduplicated list of supported channel names."""
    return list({a.channel_name for a in _ADAPTERS.values()})
