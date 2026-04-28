from __future__ import annotations

from helm.profiles.loader import ProfileLoader
from helm.profiles.schema import AgentProfile


class ProfileRegistry:
    def __init__(self, loader: ProfileLoader):
        self.loader = loader
        self._cache: dict[str, AgentProfile] = {}

    def get(self, profile_id: str) -> AgentProfile:
        if profile_id not in self._cache:
            self._cache[profile_id] = self.loader.load(profile_id)
        return self._cache[profile_id]
