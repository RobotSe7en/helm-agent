from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from helm.tools.base import ToolResult


@dataclass(slots=True)
class FileListTool:
    root: Path
    name: str = "filesystem.list"
    description: str = "List files and directories inside the project root."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path inside the project root. Use . for the project root.",
                    "default": ".",
                },
            },
        }

    async def run(self, **kwargs: object) -> ToolResult:
        path = self._resolve(str(kwargs.get("path") or "."))
        if not path.is_dir():
            return ToolResult(ok=False, content=f"Not a directory: {path}")
        entries = []
        for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            kind = "dir" if item.is_dir() else "file"
            entries.append(f"{kind}\t{item.name}")
        return ToolResult(ok=True, content="\n".join(entries))

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        root = self.root.resolve()
        if root not in target.parents and target != root:
            raise PermissionError(f"Path escapes project root: {path}")
        return target


@dataclass(slots=True)
class FileReadTool:
    root: Path
    name: str = "filesystem.read"
    description: str = "Read a UTF-8 text file inside the project root."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path inside the project root."},
            },
            "required": ["path"],
        }

    async def run(self, **kwargs: object) -> ToolResult:
        path = self._resolve(str(kwargs["path"]))
        return ToolResult(ok=True, content=path.read_text(encoding="utf-8"))

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        root = self.root.resolve()
        if root not in target.parents and target != root:
            raise PermissionError(f"Path escapes project root: {path}")
        return target


@dataclass(slots=True)
class FileWriteTool:
    root: Path
    name: str = "filesystem.write"
    description: str = "Write a UTF-8 text file inside the project root."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path inside the project root."},
                "content": {"type": "string", "description": "Text content to write."},
            },
            "required": ["path", "content"],
        }

    async def run(self, **kwargs: object) -> ToolResult:
        path = self._resolve(str(kwargs["path"]))
        content = str(kwargs.get("content") or "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, content=f"Wrote {path}")

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        root = self.root.resolve()
        if root not in target.parents and target != root:
            raise PermissionError(f"Path escapes project root: {path}")
        return target
