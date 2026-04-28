from __future__ import annotations

from helm.skills.loader import SkillLoader
from helm.skills.schema import Skill


class SkillRegistry:
    def __init__(self, loader: SkillLoader):
        self.loader = loader
        self._cache: dict[str, Skill] = {}

    def get(self, skill_id: str) -> Skill:
        if skill_id not in self._cache:
            self._cache[skill_id] = self.loader.load(skill_id)
        return self._cache[skill_id]
