from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Skill:
    id: str
    name: str
    root: Path
    instructions: str
    description: str = ""
    tool_requirements: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    config: dict[str, object] = field(default_factory=dict)
