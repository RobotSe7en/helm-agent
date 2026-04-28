from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from helm.tools.base import ToolResult
from helm.tools.shell import ShellRunTool


@dataclass(slots=True)
class GitStatusTool:
    root: Path
    name: str = "git.status"
    description: str = "Show git status."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {"type": "object", "properties": {}}

    async def run(self, **kwargs: object) -> ToolResult:
        return await ShellRunTool(self.root).run(command="git status --short")


@dataclass(slots=True)
class GitDiffTool:
    root: Path
    name: str = "git.diff"
    description: str = "Show git diff."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {"type": "object", "properties": {}}

    async def run(self, **kwargs: object) -> ToolResult:
        return await ShellRunTool(self.root).run(command="git diff")
