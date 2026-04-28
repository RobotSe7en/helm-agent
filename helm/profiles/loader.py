from __future__ import annotations

from pathlib import Path

import yaml

from helm.profiles.schema import AgentProfile


class ProfileLoader:
    def __init__(self, profile_dir: Path):
        self.profile_dir = profile_dir

    def load(self, profile_id: str) -> AgentProfile:
        root = self.profile_dir / profile_id
        if not root.exists():
            root = Path(__file__).resolve().parent / "builtin" / profile_id
        if not root.exists():
            raise FileNotFoundError(f"Profile not found: {profile_id}")

        config = self._read_yaml(root / "config.yaml")
        return AgentProfile(
            id=str(config.get("id") or profile_id),
            name=str(config.get("name") or profile_id),
            root=root,
            profile=self._read_text(root / "profile.md"),
            soul=self._read_text(root / "soul.md", required=False),
            memory=self._read_text(root / "memory.md", required=False),
            provider=config.get("provider"),
            model=config.get("model"),
            skills=list(config.get("skills") or []),
            default_toolsets=list(config.get("default_toolsets") or []),
            max_iterations=config.get("max_iterations"),
            config=config,
        )

    def _read_text(self, path: Path, required: bool = True) -> str:
        if not path.exists():
            if required:
                raise FileNotFoundError(path)
            return ""
        return path.read_text(encoding="utf-8")

    def _read_yaml(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
