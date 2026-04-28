from __future__ import annotations

from pathlib import Path

import yaml

from helm.skills.schema import Skill


class SkillLoader:
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir

    def load(self, skill_id: str) -> Skill:
        root = self.skill_dir / skill_id
        if not root.exists():
            root = Path(__file__).resolve().parent / "builtin" / skill_id
        if not root.exists():
            raise FileNotFoundError(f"Skill not found: {skill_id}")

        config = self._read_yaml(root / "config.yaml")
        return Skill(
            id=str(config.get("id") or skill_id),
            name=str(config.get("name") or skill_id),
            root=root,
            instructions=(root / "SKILL.md").read_text(encoding="utf-8"),
            description=str(config.get("description") or ""),
            tool_requirements=list(config.get("tool_requirements") or []),
            triggers=list(config.get("triggers") or []),
            config=config,
        )

    def _read_yaml(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
