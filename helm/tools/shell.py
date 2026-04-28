from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path

from helm.tools.base import ToolResult


@dataclass(slots=True)
class ShellRunTool:
    root: Path
    name: str = "shell.run"
    description: str = "Run a shell command in the project root."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run."},
            },
            "required": ["command"],
        }

    async def run(self, **kwargs: object) -> ToolResult:
        command = str(kwargs["command"])
        shell_command = command
        if os.name == "nt":
            shell_command = (
                "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
                "$OutputEncoding=[System.Text.Encoding]::UTF8; "
                f"{command}"
            )
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-Command",
                shell_command,
                cwd=self.root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            process = await asyncio.create_subprocess_shell(
                shell_command,
                cwd=self.root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        stdout, stderr = await process.communicate()
        return ToolResult(
            ok=process.returncode == 0,
            content=(stdout + stderr).decode("utf-8", errors="replace"),
            metadata={"returncode": process.returncode},
        )
