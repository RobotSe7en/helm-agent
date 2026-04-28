from __future__ import annotations

from helm.profiles.schema import AgentProfile
from helm.skills.schema import Skill


class PromptBuilder:
    def build_system_prompt(self, profile: AgentProfile, skills: list[Skill]) -> str:
        parts = [
            "# Agent Profile",
            profile.profile.strip(),
        ]
        if profile.soul.strip():
            parts.extend(["# Soul", profile.soul.strip()])
        if profile.memory.strip():
            parts.extend(["# Memory", profile.memory.strip()])
        if skills:
            parts.append("# Active Skills")
            for skill in skills:
                parts.append(f"## {skill.name}\nPath: {skill.root}\n{skill.instructions.strip()}")
        return "\n\n".join(parts)
