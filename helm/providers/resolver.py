from __future__ import annotations

from helm.config.settings import Settings
from helm.profiles.schema import AgentProfile
from helm.providers.base import Provider
from helm.providers.registry import ProviderRegistry


class ProviderResolver:
    def __init__(self, registry: ProviderRegistry, settings: Settings):
        self.registry = registry
        self.settings = settings

    def resolve(self, profile: AgentProfile, requested: str | None = None) -> Provider:
        provider_id = requested or profile.provider or self.settings.default_provider
        return self.registry.get(provider_id)
