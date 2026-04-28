from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RuntimeResult:
    status: str
    output: str
    events: list[dict[str, object]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None
