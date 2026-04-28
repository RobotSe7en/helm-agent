from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class ToolResult:
    ok: bool
    content: str
    metadata: dict[str, object] = field(default_factory=dict)


class Tool(Protocol):
    name: str
    description: str
    parameters: dict[str, object]

    async def run(self, **kwargs: object) -> ToolResult:
        ...
