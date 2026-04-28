from __future__ import annotations

from helm.providers.base import Provider
from helm.providers.echo import EchoProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, Provider] = {}
        self.register(EchoProvider())

    def register(self, provider: Provider) -> None:
        self._providers[provider.id] = provider

    def get(self, provider_id: str) -> Provider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {provider_id}") from exc
