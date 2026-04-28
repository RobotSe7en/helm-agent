from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AgentProfile:
    id: str
    name: str
    root: Path
    profile: str
    soul: str = ""
    memory: str = ""
    provider: str | None = None
    model: str | None = None
    skills: list[str] = field(default_factory=list)
    default_toolsets: list[str] = field(default_factory=list)
    max_iterations: int | None = None
    config: dict[str, object] = field(default_factory=dict)
